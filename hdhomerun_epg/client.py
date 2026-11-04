import datetime
import logging
import random
import time
import xml.etree.ElementTree as ET
import requests
import pytz
from typing import List, Dict, Optional, Any, Tuple
from .config import settings
from .cache import CacheManager
from .official import OFFICIAL_XMLTV_URL, enrich, parse_details

logger = logging.getLogger(__name__)

OFFICIAL_FEED = "official_xmltv"
# SiliconDust asks for this feed to be refreshed every 20 to 28 hours, at a
# random time: https://info.hdhomerun.com/info/dvr:xmltv
OFFICIAL_REFRESH_SECONDS = (20 * 3600, 28 * 3600)
OFFICIAL_RETRY_SECONDS = 3600
# guide.php answers 400 Bad Request for a Start past the end of the guide it
# offers, such as 48 hours ahead on a tuner without a DVR subscription.
END_OF_GUIDE_STATUS = 400


class HDHomeRunClient:
    # The first Start that guide.php refused as past the end of its guide, and
    # when: (Start, Unix time). The guide window moves forward with the clock,
    # so that Start is asked again once a chunk's time has passed. Kept for
    # the process, so the requests in between skip the call.
    _guide_end: Optional[Tuple[int, float]] = None

    def __init__(self, host: str):
        self.host = host
        self.device_auth: Optional[str] = None

    def discover_device_auth(self) -> str:
        """Discover HDHomeRun device auth."""
        logger.info("🔍 Fetching HDHomeRun Web API Device Auth")
        try:
            url = f"http://{self.host}/discover.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "DeviceAuth" in data:
                self.device_auth = data["DeviceAuth"]
                logger.info("🔑 HDHomeRun device discovered")
                return self.device_auth

            for key in data:  # Fallback if structure is different
                if "DeviceAuth" in key:  # Original code logic
                    self.device_auth = data["DeviceAuth"]
                    return self.device_auth

            raise Exception("DeviceAuth not found in discovery response")
        except Exception as e:
            logger.error(f"🚨 Error discovering device: {e}")
            raise

    def fetch_channels(self) -> List[Dict[str, Any]]:
        """Fetch EPG channels from HDHomeRun device."""
        if not self.device_auth:
            self.discover_device_auth()

        logger.info("📺 Fetching HDHomeRun lineup")
        url = f"http://{self.host}/lineup.json"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"🚨 Error fetching channels: {e}")
            raise

    @classmethod
    def _known_guide_end(cls, now: float, chunk_seconds: int) -> Optional[int]:
        """The Start refused by an earlier 400, if less than a chunk ago."""
        if cls._guide_end is None:
            return None
        refused_start, refused_at = cls._guide_end
        if now - refused_at >= chunk_seconds:
            return None
        return refused_start

    def fetch_epg_data(self, days: int, hours: int) -> Dict[str, Any]:
        """Fetch guide data for all tuned channels."""
        if not self.device_auth:
            self.discover_device_auth()

        channels = self.fetch_channels()
        cache = None
        if settings.cache_enabled:
            cache = CacheManager(settings.cache_db_path)
        else:
            logger.info("⚠️ Caching is DISABLED via configuration.")

        epg_data = {"channels": [], "programmes": []}
        seen_programmes = set()

        url = f"https://api.hdhomerun.com/api/guide.php?DeviceAuth={self.device_auth}"

        # Start with the now
        now = datetime.datetime.now(pytz.UTC)

        # Align time to grid based on chunk size (hours) to maximize cache hits
        # This converts e.g. 14:53 -> 12:00 (if hours=3) ensuring stable cache keys
        chunk_seconds = hours * 3600
        timestamp = now.timestamp()
        aligned_timestamp = timestamp - (timestamp % chunk_seconds)
        next_start_date = datetime.datetime.fromtimestamp(
            aligned_timestamp, tz=pytz.UTC
        )

        logger.info("🚀 Fetching guide data")
        # End with the desired number of days
        end_time = next_start_date + datetime.timedelta(days=days)
        first_start = int(aligned_timestamp)
        known_end = self._known_guide_end(timestamp, chunk_seconds)
        # A fetched chunk is cached once the guide is known to go on past it:
        # the chunk that runs past the end of the guide misses part of its span.
        pending_chunk = None

        # Requests session for efficiency
        session = requests.Session()
        try:
            while next_start_date < end_time:
                url_start_date = int(next_start_date.timestamp())
                if known_end and url_start_date >= known_end:
                    logger.info(f"🏁 The guide ends before {next_start_date}.")
                    break
                fetch_url = f"{url}&Start={url_start_date}"

                logger.debug(
                    f"📅 Fetching EPG for all channels starting {next_start_date}"
                )

                epg_segment = None
                if cache:
                    epg_segment = cache.get_chunk(
                        url_start_date, settings.cache_ttl_seconds
                    )

                if not epg_segment:
                    if cache:
                        logger.info(
                            f"❌ Cache miss or stale for {next_start_date}. Fetching from API."
                        )
                    else:
                        logger.info(
                            f"📡 Fetching {next_start_date} from API (Cache Disabled)."
                        )

                    try:
                        response = session.get(fetch_url, timeout=30, verify=True)
                        response.raise_for_status()
                        epg_segment = response.json()
                    except requests.RequestException as e:
                        status = getattr(e.response, "status_code", None)
                        if (
                            status == END_OF_GUIDE_STATUS
                            and url_start_date > first_start
                        ):
                            logger.info(
                                f"🏁 The guide ends before {next_start_date}: "
                                "guide.php has no data that far ahead."
                            )
                            HDHomeRunClient._guide_end = (url_start_date, timestamp)
                            break
                        logger.error(
                            f"🚨 Guide provider request failed: {type(e).__name__}"
                        )
                        # The upstream exception contains the DeviceAuth URL.
                        raise RuntimeError("Guide provider request failed") from None
                    if pending_chunk:
                        cache.save_chunk(*pending_chunk)
                    if cache:
                        chunk_end_time = int(
                            (
                                next_start_date + datetime.timedelta(hours=hours)
                            ).timestamp()
                        )
                        pending_chunk = (url_start_date, chunk_end_time, epg_segment)
                else:
                    logger.info(
                        f"✅ Cache hit for {next_start_date} (Key: {url_start_date})."
                    )
                    if pending_chunk:
                        cache.save_chunk(*pending_chunk)
                        pending_chunk = None

                logger.info(
                    f"⚙️ Processing ({next_start_date} - {next_start_date + datetime.timedelta(hours=hours)})"
                )

                for channel_epg_segment in epg_segment:
                    programmes_list = channel_epg_segment.get("Guide", [])

                    # Find matching channel in tuned channels
                    channel_info = next(
                        (
                            ch
                            for ch in channels
                            if ch.get("GuideNumber")
                            == channel_epg_segment.get("GuideNumber")
                        ),
                        None,
                    )

                    if not channel_info:
                        logger.debug(
                            f"Skipping program for untuned channel {channel_epg_segment.get('GuideNumber')}"
                        )
                        continue

                    # Add channel to epg_data if not present
                    existing_channel = next(
                        (
                            ch
                            for ch in epg_data["channels"]
                            if ch.get("GuideNumber")
                            == channel_epg_segment.get("GuideNumber")
                        ),
                        None,
                    )
                    if not existing_channel:
                        # Merge image from EPG if available
                        channel_info["ImageURL"] = channel_epg_segment.get(
                            "ImageURL", ""
                        )
                        # The network name, e.g. "Rai 3" for a regional "RAI3RLO".
                        if channel_epg_segment.get("Affiliate"):
                            channel_info["Affiliate"] = channel_epg_segment["Affiliate"]
                        epg_data["channels"].append(channel_info)

                    for programme in programmes_list:
                        signature = (
                            programme["StartTime"],
                            programme["Title"],
                            channel_epg_segment["GuideNumber"],
                        )
                        if signature in seen_programmes:
                            continue
                        seen_programmes.add(signature)

                        programme["GuideNumber"] = channel_epg_segment["GuideNumber"]
                        epg_data["programmes"].append(programme)

                next_start_date += datetime.timedelta(hours=hours)
            else:
                # The requested days ended inside the guide: the last chunk is whole.
                if pending_chunk:
                    cache.save_chunk(*pending_chunk)

        except Exception as e:
            logger.error(f"Error fetching EPG: {e}")
            # A failed fetch must not replace the last good guide with partial XML.
            raise RuntimeError("Guide data is temporarily unavailable") from None

        # The official feed is fetched about once a day, so it needs the cache.
        if cache and epg_data["programmes"]:
            epg_data["programmes"] = enrich(
                epg_data["programmes"], self.fetch_official_details(cache)
            )

        return epg_data

    def fetch_official_details(self, cache: CacheManager) -> dict[str, Any]:
        """
        Programme details from SiliconDust's own XMLTV feed, kept in the cache
        for 20 to 28 hours. Without the feed, programmes keep guide.php's details.
        """
        cached = cache.get_feed(OFFICIAL_FEED)
        if cached and cached["expires_at"] > time.time():
            return cached["data"]

        old_details = cached["data"] if cached else {}
        try:
            response = requests.get(
                OFFICIAL_XMLTV_URL, params={"DeviceAuth": self.device_auth}, timeout=60
            )
            response.raise_for_status()
            details = parse_details(response.content)
        except (requests.RequestException, ET.ParseError, ValueError, TypeError) as e:
            # Request errors quote the URL, which carries the DeviceAuth.
            status = getattr(getattr(e, "response", None), "status_code", None)
            logger.warning(
                f"⚠️ SiliconDust's XMLTV feed is unavailable ({type(e).__name__}"
                f"{f' {status}' if status else ''}); retrying in an hour."
            )
            cache.save_feed(
                OFFICIAL_FEED, old_details, int(time.time()) + OFFICIAL_RETRY_SECONDS
            )
            return old_details

        logger.info(
            f"📰 Fetched SiliconDust's XMLTV feed: {len(details)} programme entries"
        )
        cache.save_feed(
            OFFICIAL_FEED,
            details,
            int(time.time()) + random.randint(*OFFICIAL_REFRESH_SECONDS),
        )
        return details

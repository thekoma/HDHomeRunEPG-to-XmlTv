import datetime
import logging
import requests
import pytz
from typing import List, Dict, Optional, Any
from .config import settings
from .cache import CacheManager

logger = logging.getLogger(__name__)


class HDHomeRunClient:
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

        # Requests session for efficiency
        session = requests.Session()
        try:
            while next_start_date < end_time:
                url_start_date = int(next_start_date.timestamp())
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

                        # Save to cache if enabled
                        if cache:
                            chunk_end_time = int(
                                (
                                    next_start_date + datetime.timedelta(hours=hours)
                                ).timestamp()
                            )
                            cache.save_chunk(
                                url_start_date, chunk_end_time, epg_segment
                            )

                    except requests.RequestException as e:
                        logger.error(
                            f"🚨 Guide provider request failed: {type(e).__name__}"
                        )
                        # The upstream exception contains the DeviceAuth URL.
                        raise RuntimeError("Guide provider request failed") from None
                else:
                    logger.info(
                        f"✅ Cache hit for {next_start_date} (Key: {url_start_date})."
                    )

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

        except Exception as e:
            logger.error(f"Error fetching EPG: {e}")
            # A failed fetch must not replace the last good guide with partial XML.
            raise RuntimeError("Guide data is temporarily unavailable") from None

        return epg_data

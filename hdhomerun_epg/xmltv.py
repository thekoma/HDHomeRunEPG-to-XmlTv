import datetime
import xml.etree.ElementTree as ET
import logging
import re
import pytz
from typing import Any
from tzlocal import get_localzone

logger = logging.getLogger(__name__)

# Initialize local timezone
try:
    LOCAL_TZ = get_localzone()
except Exception as e:
    logger.warning(f"Could not detect local timezone: {e}. Falling back to UTC.")
    LOCAL_TZ = pytz.UTC

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>\n'
# guide.php writes episode numbers as "S09E18".
EPISODE_NUMBER = re.compile(r"S(\d+)E(\d+)")


class XMLTVGenerator:
    def __init__(self, filename: str = "epg.xml"):
        self.filename = filename
        self.root = ET.Element("tv")
        self.root.set("source-info-name", "HDHomeRun")
        self.root.set("generator-info-name", "HDHomeRunEPG_to_XmlTv_Lib")

    def create_channel(self, channel_data: dict[str, Any]) -> None:
        """Create XMLTV channel element."""
        channel_id = channel_data.get("GuideNumber", "")
        if not channel_id:
            return

        channel = ET.SubElement(self.root, "channel", id=str(channel_id))
        # Several names let media servers match the channel by name or number.
        name = channel_data.get("GuideName", "Unknown")
        names = (
            name,
            f"{channel_id} {name}",
            str(channel_id),
            channel_data.get("Affiliate"),
        )
        for display_name in dict.fromkeys(n for n in names if n):
            ET.SubElement(channel, "display-name").text = display_name
        if channel_data.get("ImageURL"):
            ET.SubElement(channel, "icon", src=channel_data["ImageURL"])

    def create_programme(
        self, programme_data: dict[str, Any], hd: bool = False
    ) -> None:
        """Create XMLTV programme element; hd marks a programme on an HD channel."""
        channel_number = programme_data.get("GuideNumber")
        if not channel_number:
            return

        try:
            start_ts = programme_data["StartTime"]
            start_time = datetime.datetime.fromtimestamp(
                start_ts, tz=pytz.UTC
            ).astimezone(LOCAL_TZ)

            end_ts = programme_data.get("EndTime", start_ts)
            duration = end_ts - start_ts
            end_time = start_time + datetime.timedelta(seconds=duration)

            programme = ET.SubElement(
                self.root,
                "programme",
                start=start_time.strftime("%Y%m%d%H%M%S %z"),
                stop=end_time.strftime("%Y%m%d%H%M%S %z"),
                channel=str(channel_number),
            )

            # Children follow the order of xmltv.dtd. guide.php does not say
            # which language a programme is in, so no lang attribute is set.
            ET.SubElement(programme, "title").text = programme_data.get("Title")

            if "EpisodeTitle" in programme_data:
                ET.SubElement(programme, "sub-title").text = programme_data[
                    "EpisodeTitle"
                ]

            if "Synopsis" in programme_data:
                ET.SubElement(programme, "desc").text = programme_data["Synopsis"]

            if "OriginalAirdate" in programme_data:
                ET.SubElement(programme, "date").text = self._air_date(
                    programme_data["OriginalAirdate"]
                )

            categories = (
                *programme_data.get("Filter", []),
                *programme_data.get("Categories", []),
            )
            for category in dict.fromkeys(categories):
                ET.SubElement(programme, "category").text = category

            if "Language" in programme_data:
                ET.SubElement(programme, "language").text = programme_data["Language"]

            images = (programme_data.get("ImageURL"), programme_data.get("PosterURL"))
            for src in dict.fromkeys(i for i in images if i):
                ET.SubElement(programme, "icon", src=src)

            if "ProgramID" in programme_data:
                ET.SubElement(
                    programme, "episode-num", system="dd_progid"
                ).text = programme_data["ProgramID"]

            if "EpisodeNumber" in programme_data:
                self._add_episode_num(programme, programme_data["EpisodeNumber"])

            if hd:
                video = ET.SubElement(programme, "video")
                ET.SubElement(video, "quality").text = "HDTV"

            self._handle_new_or_previously_shown(programme, programme_data)

            if "StarRating" in programme_data:
                rating = ET.SubElement(programme, "star-rating")
                ET.SubElement(rating, "value").text = programme_data["StarRating"]

        except Exception as e:
            logger.error(
                f"Error creating programme for {programme_data.get('Title', 'unknown')}: {e}"
            )

    @staticmethod
    def _air_date(timestamp: int) -> str:
        """
        guide.php sends the original air date as midnight UTC. January 1 means
        only the year is known: SiliconDust's own XMLTV feed writes just the year.
        """
        day = datetime.datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        if (day.month, day.day) == (1, 1):
            return day.strftime("%Y")
        return day.strftime("%Y%m%d")

    def _add_episode_num(self, programme: ET.Element, episode_number: str) -> None:
        ET.SubElement(programme, "episode-num", system="onscreen").text = episode_number
        match = EPISODE_NUMBER.fullmatch(episode_number)
        if not match:
            return
        # xmltv_ns counts from zero and leaves the part number empty: S09E18 -> "8.17."
        season, episode = (int(n) - 1 for n in match.groups())
        if season >= 0 and episode >= 0:
            ET.SubElement(
                programme, "episode-num", system="xmltv_ns"
            ).text = f"{season}.{episode}."

    def _handle_new_or_previously_shown(
        self, programme: ET.Element, data: dict[str, Any]
    ) -> None:
        """
        guide.php sets First=1 on a first airing; everything else is a repeat.
        SiliconDust's own XMLTV feed marks <new /> on the same programmes.
        """
        if data.get("First") == 1:
            ET.SubElement(programme, "new")
            return
        shown = ET.SubElement(programme, "previously-shown")
        if "OriginalAirdate" in data:
            shown.set("start", self._air_date(data["OriginalAirdate"]))

    def _build(self, epg_data: dict[str, Any]) -> None:
        channels = epg_data.get("channels", [])
        hd_channels = {str(c.get("GuideNumber")) for c in channels if c.get("HD") == 1}

        for channel in channels:
            self.create_channel(channel)

        for programme in epg_data.get("programmes", []):
            self.create_programme(
                programme, hd=str(programme.get("GuideNumber")) in hd_channels
            )

    def generate(self, epg_data: dict[str, Any]) -> str:
        """Generate XML content and return as string."""
        self._build(epg_data)
        return XML_DECLARATION + ET.tostring(self.root, encoding="unicode")

    def write_to_file(self, epg_data: dict[str, Any]) -> None:
        """Generate and write to file."""
        self._build(epg_data)
        tree = ET.ElementTree(self.root)
        ET.indent(tree, space="\t", level=0)
        tree.write(self.filename, encoding="UTF-8", xml_declaration=True)

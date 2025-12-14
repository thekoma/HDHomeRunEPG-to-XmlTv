import datetime
import xml.etree.ElementTree as ET
import logging
import pytz
from typing import Dict, Any, Optional
from tzlocal import get_localzone

logger = logging.getLogger(__name__)

# Initialize local timezone
try:
    LOCAL_TZ = get_localzone()
except Exception as e:
    logger.warning(f"Could not detect local timezone: {e}. Falling back to UTC.")
    LOCAL_TZ = pytz.UTC

class XMLTVGenerator:
    def __init__(self, filename: str = "epg.xml"):
        self.filename = filename
        self.root = ET.Element("tv")
        self.root.set("source-info-name", "HDHomeRun")
        self.root.set("generator-info-name", "HDHomeRunEPG_to_XmlTv_Lib")

    def create_channel(self, channel_data: Dict[str, Any]) -> None:
        """Create XMLTV channel element."""
        channel_id = channel_data.get("GuideNumber", "")
        if not channel_id:
            return
            
        channel = ET.SubElement(self.root, "channel", id=str(channel_id))
        ET.SubElement(channel, "display-name").text = channel_data.get("GuideName", "Unknown")
        if "ImageURL" in channel_data:
            ET.SubElement(channel, "icon", src=channel_data["ImageURL"])

    def create_programme(self, programme_data: Dict[str, Any]) -> None:
        """Create XMLTV programme element."""
        channel_number = programme_data.get("GuideNumber")
        if not channel_number:
            return

        try:
            start_ts = programme_data["StartTime"]
            start_time = datetime.datetime.fromtimestamp(start_ts, tz=pytz.UTC).astimezone(LOCAL_TZ)
            
            end_ts = programme_data.get("EndTime", start_ts)
            duration = end_ts - start_ts
            end_time = start_time + datetime.timedelta(seconds=duration)

            programme = ET.SubElement(
                self.root,
                "programme",
                start=start_time.strftime("%Y%m%d%H%M%S %z"),
                stop=end_time.strftime("%Y%m%d%H%M%S %z"),
                channel=str(channel_number)
            )

            ET.SubElement(programme, "title", lang="en").text = programme_data.get("Title")
            
            if "EpisodeTitle" in programme_data:
                ET.SubElement(programme, "sub-title", lang="en").text = programme_data["EpisodeTitle"]
                
            if "Synopsis" in programme_data:
                ET.SubElement(programme, "desc", lang="en").text = programme_data["Synopsis"]

            if "Filter" in programme_data:
                for filter_item in programme_data["Filter"]:
                    ET.SubElement(programme, "category", lang="en").text = filter_item

            if "ImageURL" in programme_data:
                ET.SubElement(programme, "icon", src=programme_data["ImageURL"])

            if "EpisodeNumber" in programme_data:
                self._add_episode_num(programme, programme_data["EpisodeNumber"])

            self._add_previously_shown(programme, programme_data, start_time)

            if programme_data.get("First") is True:
                ET.SubElement(programme, "new")

        except Exception as e:
            logger.error(f"Error creating programme for {programme_data.get('Title', 'unknown')}: {e}")

    def _add_episode_num(self, programme: ET.Element, episode_number: str) -> None:
        try:
            ET.SubElement(programme, "episode-num", system="onscreen").text = episode_number
            # Try parsing SxxExx
            if "S" in episode_number and "E" in episode_number:
                # Basic parsing like in original script
                s_idx = episode_number.index("S")
                e_idx = episode_number.index("E")
                series = int(episode_number[s_idx + 1:e_idx]) - 1
                episode = int(episode_number[e_idx + 1:]) - 1
                ET.SubElement(programme, "episode-num", system="xmltv_ns").text = f"{series}.{episode}.0/0"
        except (ValueError, IndexError):
            pass

    def _add_previously_shown(self, programme: ET.Element, data: Dict[str, Any], start_time: datetime.datetime) -> None:
        if "OriginalAirdate" in data:
            air_date = datetime.datetime.fromtimestamp(data["OriginalAirdate"], tz=pytz.UTC).astimezone(LOCAL_TZ)
            start_date_only = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            if air_date != start_date_only:
                 ET.SubElement(programme, "previously-shown").set("start", air_date.strftime("%Y%m%d%H%M%S"))
            elif data.get("First") is not True:
                 ET.SubElement(programme, "previously-shown")

    def generate(self, epg_data: Dict[str, Any]) -> str:
        """Generate XML content and return as string."""
        for channel in epg_data.get("channels", []):
            self.create_channel(channel)
            
        for programme in epg_data.get("programmes", []):
            self.create_programme(programme)
            
        return ET.tostring(self.root, encoding="unicode")

    def write_to_file(self, epg_data: Dict[str, Any]) -> None:
        """Generate and write to file."""
        for channel in epg_data.get("channels", []):
            self.create_channel(channel)
            
        for programme in epg_data.get("programmes", []):
            self.create_programme(programme)
            
        tree = ET.ElementTree(self.root)
        ET.indent(tree, space="\t", level=0)
        tree.write(self.filename, encoding="UTF-8", xml_declaration=True)

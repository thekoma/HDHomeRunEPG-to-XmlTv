"""Programme details from SiliconDust's own XMLTV feed (api/xmltv).

guide.php stays the source of the schedule and of the channel ids. This feed
only fills in what guide.php leaves out: on a real tuner it has descriptions
for 95% of programmes instead of 54%, more categories, the language, and
Schedules Direct programme ids. It cannot replace guide.php: it repeats one
channel id on several channel numbers, and its ids differ from ours.
"""

import datetime
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Any

OFFICIAL_XMLTV_URL = "https://api.hdhomerun.com/api/xmltv"


def detail_key(guide_number: Any, start: Any) -> str:
    return f"{guide_number}|{start}"


def parse_details(xml: bytes | str) -> dict[str, dict[str, Any]]:
    """Index the feed's programme details by channel number and start time."""
    root = ET.fromstring(xml)

    numbers = defaultdict(list)
    for channel in root.iter("channel"):
        numbers[channel.get("id")] += [n.text for n in channel.findall("lcn") if n.text]

    details = {}
    for programme in root.iter("programme"):
        channel_numbers = numbers.get(programme.get("channel"))
        if not channel_numbers:
            continue
        start = datetime.datetime.strptime(programme.get("start"), "%Y%m%d%H%M%S %z")
        programme_details = _details(programme)
        for number in channel_numbers:
            details[detail_key(number, int(start.timestamp()))] = programme_details
    return details


def _details(programme: ET.Element) -> dict[str, Any]:
    """Read one programme, using guide.php's field names where they exist."""
    fields = {
        "EpisodeTitle": programme.findtext("sub-title"),
        "Synopsis": programme.findtext("desc"),
        "Categories": [c.text for c in programme.findall("category") if c.text],
        "Language": programme.findtext("language"),
        "ProgramID": programme.findtext("episode-num[@system='dd_progid']"),
        "StarRating": programme.findtext("star-rating/value"),
    }
    return {name: value for name, value in fields.items() if value}


def enrich(
    programmes: list[dict[str, Any]], details: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Add the official details to each programme; guide.php's own values win."""
    return [
        {**details.get(detail_key(p.get("GuideNumber"), p.get("StartTime")), {}), **p}
        for p in programmes
    ]

import pytest
import xml.etree.ElementTree as ET
from hdhomerun_epg.xmltv import XMLTVGenerator

def test_xmltv_generation():
    epg_data = {
        "channels": [
            {"GuideNumber": "1.1", "GuideName": "Channel One", "ImageURL": "http://img/1.png"}
        ],
        "programmes": [
            {
                "GuideNumber": "1.1",
                "StartTime": 1700000000,
                "EndTime": 1700003600,
                "Title": "News",
                "EpisodeTitle": "Morning Update",
                "Synopsis": "News synopsis",
                "ImageURL": "http://img/prog.png"
            }
        ]
    }
    
    generator = XMLTVGenerator(epg_data)
    xml_str = generator.generate(epg_data)
    
    # Parse back to verify
    root = ET.fromstring(xml_str)
    assert root.tag == "tv"
    
    # Check Channel
    channel = root.find("channel")
    assert channel.get("id") == "1.1"
    assert channel.find("display-name").text == "Channel One"
    assert channel.find("icon").get("src") == "http://img/1.png"
    
    # Check Programme
    prog = root.find("programme")
    assert prog.get("channel") == "1.1"
    assert prog.find("title").text == "News"
    assert prog.find("sub-title").text == "Morning Update"
    assert prog.find("desc").text == "News synopsis"
    assert prog.find("icon").get("src") == "http://img/prog.png"

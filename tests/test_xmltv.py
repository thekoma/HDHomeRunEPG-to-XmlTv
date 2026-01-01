import xml.etree.ElementTree as ET
from hdhomerun_epg.xmltv import XMLTVGenerator


def test_xmltv_generation():
    epg_data = {
        "channels": [
            {
                "GuideNumber": "1.1",
                "GuideName": "Channel One",
                "ImageURL": "http://img/1.png",
            }
        ],
        "programmes": [
            {
                "GuideNumber": "1.1",
                "StartTime": 1700000000,
                "EndTime": 1700003600,
                "Title": "News",
                "EpisodeTitle": "Morning Update",
                "Synopsis": "News synopsis",
                "ImageURL": "http://img/prog.png",
            }
        ],
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


def test_xmltv_new_logic():
    import time
    import datetime

    now = int(time.time())

    # CASE 1: Recent OriginalAirdate (today) -> Should be <new />
    epg_new = {
        "channels": [{"GuideNumber": "1.1", "GuideName": "C1"}],
        "programmes": [
            {
                "GuideNumber": "1.1",
                "StartTime": now,
                "EndTime": now + 1800,
                "Title": "New Show",
                "OriginalAirdate": now,  # Today
            }
        ],
    }

    gen_new = XMLTVGenerator()
    xml_new = gen_new.generate(epg_new)
    root_new = ET.fromstring(xml_new)
    prog_new = root_new.find("programme")
    assert prog_new.find("new") is not None
    assert prog_new.find("previously-shown") is None

    # CASE 2: Old OriginalAirdate -> Should be <previously-shown />
    old_ts = int((datetime.datetime.now() - datetime.timedelta(days=100)).timestamp())
    epg_old = {
        "channels": [{"GuideNumber": "1.1", "GuideName": "C1"}],
        "programmes": [
            {
                "GuideNumber": "1.1",
                "StartTime": now,
                "EndTime": now + 1800,
                "Title": "Old Show",
                "OriginalAirdate": old_ts,
            }
        ],
    }

    gen_old = XMLTVGenerator()
    xml_old = gen_old.generate(epg_old)
    root_old = ET.fromstring(xml_old)
    prog_old = root_old.find("programme")
    assert prog_old.find("new") is None
    assert prog_old.find("previously-shown") is not None

    # CASE 3: No OriginalAirdate -> Should be <previously-shown />
    epg_none = {
        "channels": [{"GuideNumber": "1.1", "GuideName": "C1"}],
        "programmes": [
            {
                "GuideNumber": "1.1",
                "StartTime": now,
                "EndTime": now + 1800,
                "Title": "Mystery Show",
            }
        ],
    }

    gen_none = XMLTVGenerator()
    xml_none = gen_none.generate(epg_none)
    root_none = ET.fromstring(xml_none)
    prog_none = root_none.find("programme")
    assert prog_none.find("new") is None
    assert prog_none.find("previously-shown") is not None

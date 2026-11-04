import xml.etree.ElementTree as ET

from hdhomerun_epg.xmltv import XMLTVGenerator

# Child order of <programme> in xmltv.dtd, for the elements we emit.
PROGRAMME_ORDER = [
    "title",
    "sub-title",
    "desc",
    "date",
    "category",
    "language",
    "icon",
    "episode-num",
    "video",
    "previously-shown",
    "new",
    "star-rating",
]


def generate(channels, programmes):
    xml = XMLTVGenerator().generate({"channels": channels, "programmes": programmes})
    return xml, ET.fromstring(xml)


def programme(**fields):
    return {
        "GuideNumber": "1.1",
        "StartTime": 1700000000,
        "EndTime": 1700003600,
        "Title": "Show",
        **fields,
    }


def test_xmltv_generation():
    xml, root = generate(
        [
            {
                "GuideNumber": "1.1",
                "GuideName": "Channel One",
                "ImageURL": "http://img/1.png",
            }
        ],
        [
            programme(
                Title="News",
                EpisodeTitle="Morning Update",
                Synopsis="News synopsis",
                ImageURL="http://img/prog.png",
                Filter=["News"],
            )
        ],
    )

    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert root.tag == "tv"

    channel = root.find("channel")
    assert channel.get("id") == "1.1"
    assert [n.text for n in channel.findall("display-name")] == [
        "Channel One",
        "1.1 Channel One",
        "1.1",
    ]
    assert channel.find("icon").get("src") == "http://img/1.png"
    assert channel.find("lcn") is None  # not in xmltv.dtd

    prog = root.find("programme")
    assert prog.get("channel") == "1.1"
    assert prog.find("title").text == "News"
    assert prog.find("sub-title").text == "Morning Update"
    assert prog.find("desc").text == "News synopsis"
    assert prog.find("category").text == "News"
    assert prog.find("icon").get("src") == "http://img/prog.png"


def test_no_language_is_claimed():
    # guide.php does not say which language a programme is in.
    _, root = generate(
        [{"GuideNumber": "1.1", "GuideName": "C1"}],
        [programme(EpisodeTitle="E", Synopsis="S", Filter=["News"])],
    )
    assert not [el.tag for el in root.iter() if "lang" in el.attrib]


def test_channel_without_logo_has_no_icon():
    _, root = generate([{"GuideNumber": "7", "GuideName": "Seven", "ImageURL": ""}], [])
    assert root.find("channel/icon") is None


def test_channel_affiliate_is_an_extra_name():
    _, root = generate(
        [
            {"GuideNumber": "3", "GuideName": "RAI3RLO", "Affiliate": "Rai 3"},
            {"GuideNumber": "4", "GuideName": "Rete 4", "Affiliate": "Rete 4"},
        ],
        [],
    )
    rai3, rete4 = root.findall("channel")
    assert [n.text for n in rai3.findall("display-name")] == [
        "RAI3RLO",
        "3 RAI3RLO",
        "3",
        "Rai 3",
    ]
    assert [n.text for n in rete4.findall("display-name")] == [
        "Rete 4",
        "4 Rete 4",
        "4",
    ]


def test_episode_numbers():
    _, root = generate(
        [{"GuideNumber": "1.1", "GuideName": "C1"}],
        [programme(EpisodeNumber="S09E18"), programme(EpisodeNumber="S00E01")],
    )
    regular, special = root.findall("programme")
    assert regular.find("episode-num[@system='onscreen']").text == "S09E18"
    assert regular.find("episode-num[@system='xmltv_ns']").text == "8.17."
    # Season 0 has no zero-based xmltv_ns form; the onscreen number stays.
    assert special.find("episode-num[@system='onscreen']").text == "S00E01"
    assert special.find("episode-num[@system='xmltv_ns']") is None


def test_original_air_date():
    _, root = generate(
        [{"GuideNumber": "1.1", "GuideName": "C1"}],
        [
            programme(OriginalAirdate=1554422400),  # 2019-04-05
            programme(OriginalAirdate=1514764800),  # 2018-01-01: only the year is known
            programme(),
        ],
    )
    episode, movie, unknown = root.findall("programme")
    assert episode.find("date").text == "20190405"
    assert movie.find("date").text == "2018"
    assert unknown.find("date") is None


def test_new_follows_first_airing_flag():
    _, root = generate(
        [{"GuideNumber": "1.1", "GuideName": "C1"}],
        [
            programme(First=1, OriginalAirdate=1554422400),
            programme(OriginalAirdate=1554422400),
            programme(),
        ],
    )
    first, repeat, unknown = root.findall("programme")

    assert first.find("new") is not None
    assert first.find("previously-shown") is None

    assert repeat.find("new") is None
    assert repeat.find("previously-shown").get("start") == "20190405"

    assert unknown.find("new") is None
    assert unknown.find("previously-shown").get("start") is None


def test_hd_channels_mark_programmes_hdtv():
    _, root = generate(
        [
            {"GuideNumber": "1", "GuideName": "HD One", "HD": 1},
            {"GuideNumber": "2", "GuideName": "SD Two"},
        ],
        [programme(GuideNumber="1"), programme(GuideNumber="2")],
    )
    hd, sd = root.findall("programme")
    assert hd.find("video/quality").text == "HDTV"
    assert sd.find("video") is None


def test_poster_is_an_extra_icon():
    _, root = generate(
        [{"GuideNumber": "1.1", "GuideName": "C1"}],
        [programme(ImageURL="http://img/still.jpg", PosterURL="http://img/poster.jpg")],
    )
    assert [i.get("src") for i in root.findall("programme/icon")] == [
        "http://img/still.jpg",
        "http://img/poster.jpg",
    ]


def test_programme_children_follow_dtd_order():
    _, root = generate(
        [{"GuideNumber": "1.1", "GuideName": "C1", "HD": 1}],
        [
            programme(
                EpisodeTitle="E",
                Synopsis="S",
                OriginalAirdate=1554422400,
                Filter=["Drama", "Comedy"],
                ImageURL="http://img/i.jpg",
                EpisodeNumber="S01E02",
                First=1,
                Categories=["Series"],
                Language="it",
                ProgramID="EP1.2",
                StarRating="3/4",
            )
        ],
    )
    tags = [child.tag for child in root.find("programme")]
    assert tags == sorted(tags, key=PROGRAMME_ORDER.index)
    assert set(tags) == set(PROGRAMME_ORDER) - {"previously-shown"}


def test_official_details_are_written():
    _, root = generate(
        [{"GuideNumber": "3", "GuideName": "RAI3RLO"}],
        [
            programme(
                GuideNumber="3",
                Filter=["Documentary"],
                Categories=["Series", "Documentary"],
                Language="it",
                ProgramID="EP02267119.0018",
                EpisodeNumber="S01E03",
                StarRating="2.0/4.0",
            )
        ],
    )
    prog = root.find("programme")
    assert [c.text for c in prog.findall("category")] == ["Documentary", "Series"]
    assert prog.find("language").text == "it"
    assert [(e.get("system"), e.text) for e in prog.findall("episode-num")] == [
        ("dd_progid", "EP02267119.0018"),
        ("onscreen", "S01E03"),
        ("xmltv_ns", "0.2."),
    ]
    assert prog.find("star-rating/value").text == "2.0/4.0"

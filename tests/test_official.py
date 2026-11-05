import copy

from hdhomerun_epg.official import enrich, parse_details
from tests.conftest import OFFICIAL_FEED, OFFICIAL_START

DETAILS = {
    "EpisodeTitle": "L'Italia in guerra",
    "Synopsis": "Il 10 giugno 1940.",
    "Categories": ["Series", "Documentary"],
    "Language": "it",
    "ProgramID": "EP02267119.0018",
    "StarRating": "2.0/4.0",
}


def test_parse_details_indexes_every_channel_number_of_a_station():
    details = parse_details(OFFICIAL_FEED)
    assert details == {
        f"3|{OFFICIAL_START}": DETAILS,
        f"802|{OFFICIAL_START}": DETAILS,
    }


def test_enrich_fills_what_guide_php_leaves_out():
    programmes = [
        {
            "GuideNumber": "3",
            "StartTime": OFFICIAL_START,
            "Title": "1939-1945",
            "Synopsis": "Our own synopsis.",
            "Filter": ["Documentary"],
        },
        {"GuideNumber": "4", "StartTime": OFFICIAL_START, "Title": "Elsewhere"},
    ]
    before = copy.deepcopy(programmes)

    matched, unmatched = enrich(programmes, parse_details(OFFICIAL_FEED))

    assert matched == {
        **DETAILS,
        "GuideNumber": "3",
        "StartTime": OFFICIAL_START,
        "Title": "1939-1945",
        "Synopsis": "Our own synopsis.",  # guide.php's value wins
        "Filter": ["Documentary"],
    }
    assert unmatched == before[1]
    assert programmes == before  # the input is not changed

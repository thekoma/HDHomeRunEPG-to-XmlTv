from app.guide_view import build_guide_view, genre_of

NOW = 1_800_000_000  # 2027-01-15 08:00 UTC, on a half-hour boundary
ORIGIN = NOW - NOW % 1800


def test_genre_prefers_the_most_specific_category():
    assert genre_of(["Drama", "Movies"]) == "movies"
    assert genre_of(["Comedy", "Drama"]) == "comedy"
    assert genre_of(["Children"]) == "kids"
    assert genre_of(["Talk"]) == "other"
    assert genre_of(None) == "other"


def test_programmes_are_placed_on_one_time_scale():
    data = {
        "channels": [
            {"GuideNumber": "1", "GuideName": "Rai 1", "ImageURL": "logo.png"},
            {"GuideNumber": "2", "GuideName": "Rai 2", "ImageURL": ""},
        ],
        "programmes": [
            # Ended before the origin: dropped.
            {
                "GuideNumber": "1",
                "StartTime": ORIGIN - 3600,
                "EndTime": ORIGIN,
                "Title": "Old",
            },
            # Airing across the origin: clipped to start at minute 0.
            {
                "GuideNumber": "1",
                "StartTime": ORIGIN - 600,
                "EndTime": ORIGIN + 1200,
                "Title": "Tg1",
                "Filter": ["News"],
            },
            {
                "GuideNumber": "1",
                "StartTime": ORIGIN + 1200,
                "EndTime": ORIGIN + 4800,
                "Title": "Film",
                "Filter": ["Movies", "Drama"],
            },
            {
                "GuideNumber": "2",
                "StartTime": ORIGIN + 300,
                "EndTime": ORIGIN + 900,
                "Title": "Meteo",
            },
        ],
    }

    view = build_guide_view(data, NOW + 120)

    assert view["origin"] == ORIGIN
    assert view["span_min"] == 80
    rai1, rai2 = view["channels"]
    assert rai1["logo"] == "logo.png" and rai2["logo"] is None
    assert [
        (s["title"], s["start_min"], s["dur_min"], s["genre"]) for s in rai1["slots"]
    ] == [
        ("Tg1", 0, 20, "news"),
        ("Film", 20, 60, "movies"),
    ]
    assert [(s["start_min"], s["dur_min"], s["genre"]) for s in rai2["slots"]] == [
        (5, 10, "other")
    ]
    # Detail records keep the real start, not the clipped one, and point back to their row.
    tg1 = view["details"][rai1["slots"][0]["i"]]
    assert (
        tg1["start"] == ORIGIN - 600 and tg1["channel"] == "Rai 1" and tg1["row"] == 0
    )
    assert [g["key"] for g in view["genres"]] == ["news", "movies", "other"]

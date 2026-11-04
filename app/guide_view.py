"""View model for the TV guide page.

Every programme is placed on one fixed time scale, in minutes from an origin
(the start of the current half hour). The browser turns minutes into pixels,
so the same data serves every screen size.
"""

from typing import Any

HALF_HOUR = 1800

# Genre fills of the sheet, most specific first: a programme tagged
# "Movies" and "Drama" is filled as a movie.
GENRE_ORDER = ("movies", "sports", "kids", "news", "documentary", "comedy", "drama")
# Reading order of the legend.
LEGEND_ORDER = (
    "news",
    "drama",
    "comedy",
    "movies",
    "sports",
    "kids",
    "documentary",
    "other",
)
GENRE_LABELS = {
    "movies": "Movies",
    "sports": "Sports",
    "kids": "Kids",
    "news": "News",
    "documentary": "Documentary",
    "comedy": "Comedy",
    "drama": "Drama",
    "other": "Other",
}
# guide.php "Filter" values and XMLTV categories that map onto a fill.
_ALIASES = {
    "movie": "movies",
    "movies": "movies",
    "film": "movies",
    "sport": "sports",
    "sports": "sports",
    "kids": "kids",
    "children": "kids",
    "news": "news",
    "newsmagazine": "news",
    "documentary": "documentary",
    "comedy": "comedy",
    "sitcom": "comedy",
    "drama": "drama",
}


def genre_of(categories: list[str] | None) -> str:
    """Pick the sheet fill for a programme from its raw categories."""
    found = {_ALIASES.get(c.strip().lower()) for c in categories or []}
    return next((g for g in GENRE_ORDER if g in found), "other")


def build_guide_view(epg_data: dict[str, Any], now: float) -> dict[str, Any]:
    """Return channels with positioned programmes, plus the detail records."""
    origin = int(now - now % HALF_HOUR)
    by_channel: dict[str, list[dict[str, Any]]] = {}
    for prog in epg_data.get("programmes", []):
        if prog.get("EndTime", 0) > origin:
            by_channel.setdefault(prog.get("GuideNumber"), []).append(prog)

    channels, details, genres_present = [], [], set()
    span = 0
    for ch in epg_data.get("channels", []):
        number = ch.get("GuideNumber")
        slots = []
        for prog in sorted(by_channel.get(number, []), key=lambda p: p["StartTime"]):
            start = max(prog["StartTime"], origin)
            genre = genre_of(prog.get("Filter"))
            genres_present.add(genre)
            slots.append(
                {
                    "i": len(details),
                    "title": prog.get("Title", ""),
                    "start_min": (start - origin) // 60,
                    "dur_min": max((prog["EndTime"] - start) // 60, 1),
                    "start_ts": prog["StartTime"],
                    "genre": genre,
                }
            )
            details.append(
                {
                    "title": prog.get("Title", ""),
                    "episodeTitle": prog.get("EpisodeTitle"),
                    "episodeNumber": prog.get("EpisodeNumber"),
                    "synopsis": prog.get("Synopsis"),
                    "start": prog["StartTime"],
                    "end": prog["EndTime"],
                    "airdate": prog.get("OriginalAirdate"),
                    "first": bool(prog.get("First")),
                    "image": prog.get("ImageURL") or prog.get("PosterURL"),
                    "categories": prog.get("Filter") or [],
                    "genre": genre,
                    "channel": ch.get("GuideName", number),
                    "row": len(channels),
                }
            )
            span = max(span, (prog["EndTime"] - origin) // 60)
        channels.append(
            {
                "number": number,
                "name": ch.get("GuideName", number),
                "logo": ch.get("ImageURL") or None,
                "slots": slots,
            }
        )

    return {
        "origin": origin,
        "span_min": span,
        "channels": channels,
        "details": details,
        "genres": [
            {"key": g, "label": GENRE_LABELS[g]}
            for g in LEGEND_ORDER
            if g in genres_present
        ],
    }

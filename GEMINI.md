# HDHomeRun EPG: project context

A FastAPI service that reads the guide data of an HDHomeRun tuner and serves it as XMLTV for Jellyfin, Plex and Emby, plus a TV guide and a status page in the browser.

## Data flow

- `discover.json` on the tuner gives the `DeviceAuth` key and `lineup.json` the channels.
- `api.hdhomerun.com/api/guide.php` gives the schedule, 4 hours per call. Without a DVR subscription it answers `400` for a `Start` more than 48 hours ahead, and the client treats that as the end of the guide.
- `api.hdhomerun.com/api/xmltv`, SiliconDust's own XMLTV feed, fills in descriptions, categories, language, `dd_progid` and star ratings. It is fetched every 20 to 28 hours and only when the cache works.
- Chunks and the feed live in a SQLite cache (`epg_cache.db`, `/data/epg_cache.db` in the Docker image).

## Endpoints

- `GET /`: status page, or status JSON when the request accepts `application/json`.
- `GET /guide`: TV guide.
- `GET /epg.xml`: XMLTV feed.
- `GET /cache` and `DELETE /cache`: list or clear the cache.
- `GET /healthcheck`: liveness probe.
- `GET /docs`: OpenAPI documentation.

## Layout

- `app/main.py`: routes.
- `app/guide_view.py`: view model for the guide page.
- `app/templates/`: Jinja templates (`base.html`, `guide.html`, `dashboard.html`).
- `app/static/`: hand-written CSS and JavaScript and the self-hosted Archivo font. There is no build step and no CDN.
- `hdhomerun_epg/client.py`: tuner and guide requests, chunking and caching.
- `hdhomerun_epg/official.py`: parsing of SiliconDust's XMLTV feed and the merge into the schedule.
- `hdhomerun_epg/xmltv.py`: XMLTV output, which validates against `xmltv.dtd`.
- `hdhomerun_epg/cache.py`: SQLite cache.
- `hdhomerun_epg/config.py`: settings from `HDHOMERUN_*` environment variables.
- `deploy/`: Helm, Argo CD and Flux examples for the bjw-s app-template chart (see `DEPLOY.md`).
- `PRODUCT.md` and `DESIGN.md`: product context and design system for the web pages.

## Commands

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
```

Run them from the repository root. The Docker image uses Python 3.9, so code must import on 3.9: write `from __future__ import annotations` in modules that use `X | None` annotations. CI runs ruff 0.14.9, the version in `.pre-commit-config.yaml`.

## Releases

Every push to `main` publishes a GitHub release tagged `YYYY.MM.N` and pushes `ghcr.io/thekoma/hdhomerunepgxml:latest` and the tag (`.github/workflows/release_main.yml`). To ship several pull requests as one release, merge all but the last with `[skip ci]` in the merge commit subject.

## Configuration

| Variable | Default |
| --- | --- |
| `HDHOMERUN_HOST` | `hdhomerun.local` |
| `HDHOMERUN_EPG_DAYS` | `4` |
| `HDHOMERUN_EPG_HOURS` | `4` |
| `HDHOMERUN_CACHE_ENABLED` | `True` |
| `HDHOMERUN_CACHE_DB_PATH` | `epg_cache.db` |
| `HDHOMERUN_CACHE_TTL_SECONDS` | `86400` |
| `HDHOMERUN_DEBUG_MODE` | `on` |
| `HDHOMERUN_OUTPUT_FILENAME` | `epg.xml` |

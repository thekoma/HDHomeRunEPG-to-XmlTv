# HDHomeRun EPG Service - Project Context

## Project Overview
A FastAPI-based service that acts as a proxy between HDHomeRun devices and XMLTV-compatible clients (like Plex or Emby). It fetches EPG data, caches it, and serves it as XML.
Recently refactored from a single script to a modular modern web application.

## Key Features
-   **Service**: FastAPI application running on port 8000.
    -   `GET /`: Dashboard (Browser) or Status JSON (API).
    -   `GET /guide`: Rich TV Guide UI (Timeline layout, Filters, Modal).
    -   `GET /epg.xml`: XMLTV generation for external clients.
    -   `GET /healthcheck`: Liveness probe.
    -   `DELETE /cache`: Manual cache invalidation.
-   **Caching**: SQLite-based caching (`epg_cache.db`) with 24h TTL.
    -   Aligned to 4-hour chunks to maximize cache hits.
    -   Configurable via `CACHE_ENABLED=true/false`.
-   **UI/UX**:
    -   **Dashboard**: Tailwind CSS, shows cache stats and status.
    -   **Guide**: Interactive Timeline with sticky headers, search, and progress bars.
    -   **Templates**: Jinja2 used for all HTML rendering (`app/templates/`).

## Architecture
-   `app/`: FastAPI application code.
    -   `main.py`: Entry point and route definitions.
    -   `templates/`: HTML files (`dashboard.html`, `guide.html`).
-   `hdhomerun_epg/`: Core library logic.
    -   `client.py`: Handles HDHomeRun API communication and Caching integration.
    -   `xmltv.py`: Generates XMLTV string from Python objects.
    -   `cache.py`: SQLite abstraction layer.
    -   `config.py`: Pydantic Settings for env vars.
-   `tests/`: Pytest suite (coverage > 90%).

## Quick Start
1.  **Run Locally**:
    ```powershell
    uvicorn app.main:app --host 0.0.0.0 --reload
    ```
    > **Note**: Always use `.\venv` as your local environment.

2.  **Run Tests**:
    ```powershell
    pytest -v
    ```
3.  **Docker**:
    ```bash
    docker-compose up --build
    ```

## Configuration (Env Vars)
| Variable | Default | Description |
| :--- | :--- | :--- |
| `HDHOMERUN_HOST` | `10.0.1.2` | IP of the device |
| `EPG_DAYS` | `7` | Days of data to fetch |
| `CACHE_ENABLED` | `true` | Enable SQLite caching |
| `CACHE_TTL_SECONDS` | `86400` | Cache expiry (24h) |
| `DEBUG_MODE` | `off` | Verbose logging |

## Status
-   **Completed**: Refactoring, Caching, Dashboard, Guide UI, Testing, Docker.
-   **Next Steps**: Authenticated endpoints (optional), multiple device support (optional).

# HDHomeRun EPG to XMLTV

![CI Status](https://img.shields.io/github/actions/workflow/status/thekoma/HDHomeRunEPG-to-XmlTv/ci.yml?branch=main&style=flat-square&label=CI)
![GitHub Release](https://img.shields.io/github/v/release/thekoma/HDHomeRunEPG-to-XmlTv?style=flat-square&label=Release)
![Docker Image](https://img.shields.io/badge/docker-ghcr.io%2Fthekoma%2Fhdhomerunepgxml-blue?style=flat-square&logo=docker&logoColor=white)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/github/license/thekoma/HDHomeRunEPG-to-XmlTv?style=flat-square)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)

Refactored Python library and FastAPI service to fetch EPG from HDHomeRun devices and serve it as XMLTV.

## 🌟 Data Flow

1. **Discovery**: Finds the HDHomeRun device and its Auth Token.
2. **Lineup**: Fetches the channel list (`lineup.json`).
3. **EPG Fetching**: 
   - Requests EPG data in chunks (default 2 hours) to respect API limits.
   - **Smart Caching**: Checks local SQLite DB (`epg_cache.db`) before hitting the API.
   - **Time Alignment**: Requests are aligned to fixed time grids (e.g. 12:00, 14:00) to maximize cache hits.
4. **XML Generation**: Converts the JSON data into XMLTV format.

## 📊 Project Status

-   **Completed**: Refactoring, Caching, Dashboard, Guide UI, Testing, Docker.
-   **Deployment**: [Deployment Guide](DEPLOY.md) (Helm, ArgoCD, FluxCD).
-   **Next Steps**: Authenticated endpoints (optional), multiple device support (optional).

## 🚀 Usage

### 🐳 Docker (Recommended)

One official Docker image is available at `ghcr.io/thekoma/hdhomerunepgxml`.

Run the service using Docker Compose:


```bash
docker compose up --build -d
```

The XMLTV file will be available at:
`http://localhost:8000/epg.xml`

### ⚙️ Configuration

The application is fully configurable via Environment Variables.

| | Variable | Default | Description |
|-------|----------|---------|-------------|
| 🏠 | `HDHOMERUN_HOST` | `hdhomerun.local` | IP or Hostname of your HDHomeRun device. |
| 📅 | `HDHOMERUN_EPG_DAYS` | `4` | Number of days of EPG data to fetch. |
| ⏱️ | `HDHOMERUN_EPG_HOURS` | `2` | Size of each fetch chunk in hours. Smaller chunks = more granular caching. |
| 🐛 | `HDHOMERUN_DEBUG_MODE` | `on` | Enable detailed debug logging. |
| 💾 | `HDHOMERUN_CACHE_ENABLED`| `True` | Set to `False` to completely disable caching. |
| 📦 | `HDHOMERUN_CACHE_DB_PATH`| `epg_cache.db` | Path to the SQLite cache file. |
| ⏳ | `HDHOMERUN_CACHE_TTL_SECONDS`| `86400` | How long (in seconds) to keep cached data (Default: 24h). |

### ⚡ API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | **Responsive Root**. Returns **Dashboard (HTML)** for browsers or **Status (JSON)** for API clients. |
| `GET` | `/guide` | **TV Guide**. Visual TV Guide showing programs for the next 24 hours. |
| `GET` | `/epg.xml` | **Main Endpoint**. Fetches and returns the generated XMLTV file. |
| `GET` | `/healthcheck` | **Liveness**. Returns `{"status": "ok"}`. |
| `DELETE`| `/cache` | **Maintenance**. Manually clears the entire local cache. |

### 🛠️ Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the service:
   ```bash
   uvicorn app.main:app --reload
   ```


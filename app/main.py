from fastapi import FastAPI, Response, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from contextlib import asynccontextmanager
from hdhomerun_epg import HDHomeRunClient, XMLTVGenerator, settings
from app.guide_view import build_guide_view
import mimetypes
import uvicorn
import time

# Slim images ship without a MIME table that knows web fonts.
mimetypes.add_type("font/woff2", ".woff2")

# Setup Logging
logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting HDHomeRun EPG Service")
    # Configure library logger
    lib_logger = logging.getLogger("hdhomerun_epg")
    lib_logger.setLevel(logging.DEBUG if settings.debug_mode == "on" else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    lib_logger.addHandler(handler)

    yield
    logger.info("🛑 Stopping HDHomeRun EPG Service")


app = FastAPI(title="HDHomeRun EPG to XMLTV", version="2.0.0", lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/healthcheck")
def healthcheck():
    """
    Simple healthcheck endpoint.
    """
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    Root endpoint. Returns Dashboard for browsers, JSON status for API clients.
    """
    accept = request.headers.get("Accept", "")

    # Check if client explicitly wants JSON
    if "application/json" in accept:
        try:
            from hdhomerun_epg.cache import CacheManager

            cache = CacheManager(settings.cache_db_path)
            stats = cache.get_status()
            return JSONResponse(
                content={
                    "status": "online",
                    "cache_entries": len(stats),
                    "cache_size_bytes": sum(c["size_bytes"] for c in stats),
                    "chunks": stats,
                }
            )
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return JSONResponse(
                content={"status": "error", "message": str(e)}, status_code=500
            )

    # Default to Dashboard
    config_items = []
    for field_name, field_info in type(settings).model_fields.items():
        value = getattr(settings, field_name)
        default = field_info.default
        is_default = value == default
        config_items.append(
            {"name": field_name, "value": value, "is_default": is_default}
        )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "active": "status",
            "config_items": config_items,
            "cache_ttl_seconds": settings.cache_ttl_seconds,
        },
    )


@app.get("/guide", response_class=HTMLResponse)
def tv_guide(request: Request):
    """
    Render the TV guide: every programme on one time scale, coloured by genre.
    """
    logger.info("📺 Rendering TV Guide")
    context = {"active": "guide", "view": None, "error": None}
    status_code = 200
    try:
        client = HDHomeRunClient(host=settings.host)
        epg_data = client.fetch_epg_data(
            days=settings.epg_days, hours=settings.epg_hours
        )
        context["view"] = build_guide_view(epg_data, time.time())
    except Exception as e:
        logger.error(f"Error rendering guide: {e}")
        context["error"] = str(e)
        status_code = 500
    return templates.TemplateResponse(
        request=request, name="guide.html", context=context, status_code=status_code
    )


@app.get("/epg.xml")
def get_epg(background_tasks: BackgroundTasks):
    """
    Generate and retrieve the EPG in XMLTV format.
    This triggers a fresh fetch from the HDHomeRun device.
    """
    logger.info("📨 Received request for epg.xml")

    try:
        # Initialize Client
        client = HDHomeRunClient(host=settings.host)

        # Fetch Data
        epg_data = client.fetch_epg_data(
            days=settings.epg_days, hours=settings.epg_hours
        )

        # Generate XML
        generator = XMLTVGenerator()
        xml_content = generator.generate(epg_data)

        return Response(content=xml_content, media_type="application/xml")

    except Exception as e:
        logger.error(f"🚨 Error generating EPG: {e}")
        return Response(content=f"Error generating EPG: {str(e)}", status_code=500)


@app.delete("/cache")
def clear_cache():
    """
    Clear the local EPG cache.
    """
    logger.info("🗑️ Received request to clear cache")
    try:
        from hdhomerun_epg.cache import CacheManager

        cache = CacheManager(settings.cache_db_path)
        cache.clear_cache()
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"🚨 Error clearing cache: {e}")
        return Response(content=f"Error clearing cache: {str(e)}", status_code=500)


@app.get("/cache")
def get_cache_status():
    """
    Get status of the cache (JSON).
    """
    try:
        from hdhomerun_epg.cache import CacheManager

        cache = CacheManager(settings.cache_db_path)
        return cache.get_status()
    except Exception as e:
        logger.error(f"🚨 Error getting cache status: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

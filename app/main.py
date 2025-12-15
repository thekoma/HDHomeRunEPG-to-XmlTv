from fastapi import FastAPI, Response, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
from contextlib import asynccontextmanager
from hdhomerun_epg import HDHomeRunClient, XMLTVGenerator, settings
import uvicorn
import time

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
    for field_name, field_info in settings.model_fields.items():
        value = getattr(settings, field_name)
        default = field_info.default
        is_default = value == default
        config_items.append({
            "name": field_name,
            "value": value,
            "is_default": is_default
        })

    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"config_items": config_items}
    )


@app.get("/guide", response_class=HTMLResponse)
def tv_guide(request: Request):
    """
    Render a visual TV Guide using fetched EPG data.
    """
    logger.info("📺 Rendering TV Guide")
    try:
        # Fetch EPG Data (uses Cache + API)
        client = HDHomeRunClient(host=settings.host)
        # Fetch EPG days as configured to allow full timeline scrolling
        epg_data = client.fetch_epg_data(days=settings.epg_days, hours=4)

        # Prepare data for template
        channels = epg_data.get("channels", [])
        programmes = epg_data.get("programmes", [])
        programmes.sort(key=lambda x: x.get("StartTime", 0))

        from collections import defaultdict
        import datetime

        now = time.time()
        pixels_per_minute = 5  # Scale factor for width

        # Filter out past programs
        programmes = [p for p in programmes if p["EndTime"] > now]

        grouped_programmes = defaultdict(list)
        for p in programmes:
            # Pre-calculate strings for template - DEFAULT to server time, will be overridden by JS
            p["start_ts"] = p["StartTime"]
            p["end_ts"] = p["EndTime"]
            p["start_str"] = datetime.datetime.fromtimestamp(p["StartTime"]).strftime(
                "%H:%M"
            )
            p["end_str"] = datetime.datetime.fromtimestamp(p["EndTime"]).strftime(
                "%H:%M"
            )

            # --- Visual Width Calculation ---
            # For programs currently playing, we only want to show the REMAINING portion
            # starting from the left edge (Now).
            visual_start = max(p["StartTime"], now)
            visual_duration_seconds = p["EndTime"] - visual_start
            
            # Width calculation
            visual_duration_minutes = visual_duration_seconds / 60
            p["width_px"] = int(visual_duration_minutes * pixels_per_minute)

            # Progress calculation (still based on total duration)
            total_duration = p["EndTime"] - p["StartTime"]
            if now < p["StartTime"]:
                p["progress_percent"] = 0
            elif now > p["EndTime"]:
                p["progress_percent"] = 100
            else:
                p["progress_percent"] = int(
                    ((now - p["StartTime"]) / total_duration) * 100
                )

            grouped_programmes[p["GuideNumber"]].append(p)

        # --- Gap Filling Logic ---
        # Ensure programs are aligned to the timeline by inserting spacer blocks for gaps.
        # This fixes the issue where gaps cause subsequent programs to shift left (desync),
        # leaving the end of the timeline empty.
        
        timeline_end_time = now + (settings.epg_days * 24 * 60 * 60)
        
        for guide_number, progs in grouped_programmes.items():
            # Ensure sorted
            progs.sort(key=lambda x: x["StartTime"])
            
            filled_progs = []
            # Cursor tracks the end of the last added element (starting at Now)
            cursor = now
            
            for p in progs:
                # Calculate gap from cursor to program start
                # We only care if program starts after cursor.
                if p["StartTime"] > cursor:
                    gap_seconds = p["StartTime"] - cursor
                    # Only render gap if significant (> 1 minute visual)
                    if gap_seconds > 0: # render even small gaps to maintain perfect sync
                        gap_minutes = gap_seconds / 60
                        gap_px = int(gap_minutes * pixels_per_minute)
                        if gap_px > 0:
                            filled_progs.append({
                                "is_gap": True,
                                "width_px": gap_px,
                                "StartTime": cursor,
                                "EndTime": p["StartTime"],
                                "title": "No Data" # Helper
                            })
                
                filled_progs.append(p)
                # update cursor to end of this program
                cursor = max(cursor, p["EndTime"])
            
            # Optional: Fill remainder of timeline
            # if cursor < timeline_end_time:
            #     gap_seconds = timeline_end_time - cursor
            #     gap_minutes = gap_seconds / 60
            #     gap_px = int(gap_minutes * pixels_per_minute)
            #     if gap_px > 0:
            #         filled_progs.append({"is_gap": True, "width_px": gap_px})

            grouped_programmes[guide_number] = filled_progs

        # Group everything nicely
        grouped_data = {}
        for ch in channels:
            gn = ch.get("GuideNumber")
            grouped_data[gn] = {
                "channel": ch,
                "programmes": grouped_programmes.get(gn, []),
            }

        return templates.TemplateResponse(
            request=request,
            name="guide.html",
            context={
                "channels": channels, 
                "grouped_data": grouped_data,
                "epg_days": settings.epg_days
            },
        )

    except Exception as e:
        logger.error(f"Error rendering guide: {e}")
        return HTMLResponse(
            content=f"<h1>Error rendering guide</h1><p>{e}</p>", status_code=500
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

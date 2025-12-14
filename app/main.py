from fastapi import FastAPI, Response, BackgroundTasks, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
import logging
from contextlib import asynccontextmanager
from hdhomerun_epg import HDHomeRunClient, XMLTVGenerator, settings
import uvicorn
import io

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
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    lib_logger.addHandler(handler)
    
    yield
    # Shutdown
    logger.info("🛑 Stopping HDHomeRun EPG Service")

app = FastAPI(title="HDHomeRun EPG to XMLTV", version="2.0.0", lifespan=lifespan)

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
            return JSONResponse(content={
                "status": "online", 
                "cache_entries": len(stats),
                "cache_size_bytes": sum(c['size_bytes'] for c in stats),
                "chunks": stats
            })
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
    
    # Default to Dashboard
    return dashboard_html()

def dashboard_html():
    return """
    <!DOCTYPE html>
    <html lang="en" class="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HDHomeRun EPG Status</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {
              darkMode: 'class',
              theme: {
                extend: {
                  colors: {
                    slate: {
                      850: '#1e293b',
                      900: '#0f172a',
                    }
                  }
                }
              }
            }
        </script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body { font-family: 'Inter', sans-serif; }
        </style>
    </head>
    <body class="bg-slate-900 text-gray-100 min-h-screen p-8">
        <div class="max-w-6xl mx-auto">
            <header class="flex justify-between items-center mb-10">
                <div>
                    <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                        HDHomeRun EPG
                    </h1>
                    <p class="text-slate-400 mt-2">Service Status & Cache Inspector</p>
                </div>
                <div class="flex gap-4">
                    <a href="/docs" class="text-slate-400 hover:text-white transition-colors flex items-center gap-2">
                        <span>📚</span> API Docs
                    </a>
                    <button onclick="clearCache()" class="bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-6 rounded-lg shadow-lg transition-all transform hover:scale-105 flex items-center gap-2">
                        <span>🗑️</span> Clear Cache
                    </button>
                </div>
            </header>

            <!-- Status Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                    <h3 class="text-slate-400 text-sm font-semibold uppercase">Status</h3>
                    <p class="text-2xl font-bold text-green-400 mt-2 flex items-center gap-2">
                        <span class="w-3 h-3 bg-green-400 rounded-full animate-pulse"></span> Online
                    </p>
                </div>
                 <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                    <h3 class="text-slate-400 text-sm font-semibold uppercase">Cached Chunks</h3>
                    <p id="stat-chunks" class="text-2xl font-bold text-blue-400 mt-2">--</p>
                </div>
                 <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                    <h3 class="text-slate-400 text-sm font-semibold uppercase">Total Size</h3>
                    <p id="stat-size" class="text-2xl font-bold text-purple-400 mt-2">--</p>
                </div>
            </div>

            <div class="bg-slate-800 rounded-xl shadow-2xl overflow-hidden border border-slate-700">
                <div class="p-6 border-b border-slate-700 flex justify-between items-center">
                    <h2 class="text-xl font-semibold text-white">Cache Contents</h2>
                </div>
                <div class="max-h-[600px] overflow-y-auto custom-scrollbar">
                    <table class="w-full text-left border-collapse">
                        <thead class="bg-slate-800 text-slate-400 uppercase text-xs tracking-wider sticky top-0 z-10 shadow-md">
                            <tr>
                                <th class="p-3 bg-slate-800">Start Time</th>
                                <th class="p-3 bg-slate-800">End Time</th>
                                <th class="p-3 bg-slate-800">Size</th>
                                <th class="p-3 bg-slate-800">Age</th>
                                <th class="p-3 bg-slate-800">Fetched At</th>
                                <th class="p-3 bg-slate-800">Status</th>
                            </tr>
                        </thead>
                        <tbody id="cache-table-body" class="divide-y divide-slate-700">
                            <!-- Rows injected here -->
                        </tbody>
                    </table>
                </div>
                <div id="empty-state" class="p-12 text-center text-slate-500 hidden">
                    <p class="text-lg">Cache is empty 🍃</p>
                </div>
            </div>
        </div>

        <script>
            async function fetchCache() {
                try {
                    const res = await fetch('/cache');
                    const chunks = await res.json();
                    renderTable(chunks);
                    updateStats(chunks);
                } catch (e) {
                    console.error("Failed to fetch cache", e);
                }
            }

            async function clearCache() {
                if(!confirm("Are you sure you want to delete all cached data?")) return;
                try {
                    await fetch('/cache', { method: 'DELETE' });
                    fetchCache();
                } catch (e) {
                    alert("Error clearing cache");
                }
            }

            function formatBytes(bytes, decimals = 2) {
                if (!+bytes) return '0 Bytes';
                const k = 1024;
                const dm = decimals < 0 ? 0 : decimals;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
            }
            
            function updateStats(chunks) {
                document.getElementById('stat-chunks').innerText = chunks.length;
                const totalSize = chunks.reduce((acc, curr) => acc + curr.size_bytes, 0);
                document.getElementById('stat-size').innerText = formatBytes(totalSize);
            }

            function renderTable(chunks) {
                const tbody = document.getElementById('cache-table-body');
                const emptyState = document.getElementById('empty-state');
                
                tbody.innerHTML = '';

                if (!chunks || chunks.length === 0) {
                    emptyState.classList.remove('hidden');
                    return;
                } else {
                    emptyState.classList.add('hidden');
                }

                chunks.forEach(chunk => {
                    const startDate = new Date(chunk.start_time * 1000).toLocaleString();
                    const endDate = new Date(chunk.end_time * 1000).toLocaleString();
                    const fetchedDate = new Date(chunk.fetched_at * 1000).toLocaleString();
                    const ageSeconds = Math.floor((Date.now() / 1000) - chunk.fetched_at);
                    
                    let statusHtml = '<span class="text-green-400 font-bold text-xs uppercase tracking-wide">Fresh</span>';
                    if (ageSeconds > 86400) { // 24h
                        statusHtml = '<span class="text-orange-400 font-bold text-xs uppercase tracking-wide">Stale</span>';
                    }

                    const row = `
                        <tr class="hover:bg-slate-700/50 transition-colors">
                            <td class="p-4 font-mono text-sm text-blue-300">${startDate}</td>
                            <td class="p-4 font-mono text-sm text-blue-300">${endDate}</td>
                            <td class="p-4 text-slate-300">${formatBytes(chunk.size_bytes)}</td>
                            <td class="p-4 text-slate-300">${ageSeconds}s ago</td>
                            <td class="p-4 text-slate-400 text-sm">${fetchedDate}</td>
                            <td class="p-4">${statusHtml}</td>
                        </tr>
                    `;
                    tbody.innerHTML += row;
                });
            }

            // Initial load
            fetchCache();
        </script>
    </body>
    </html>
    """

@app.get("/epg.xml")
def get_epg(background_tasks: BackgroundTasks):
    """
    Generate and retrieve the EPG in XMLTV format.
    This triggers a fresh fetch from the HDHomeRun device.
    """
    logger.info("📨 Received request for epg.xml")
    
    try:
        # Initialize Client
        client = HDHomeRunClient(host=settings.hdhomerun_host)
        
        # Fetch Data
        epg_data = client.fetch_epg_data(
            days=settings.epg_days, 
            hours=settings.epg_hours
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

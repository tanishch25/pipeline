import os
import sys
import asyncio
import nest_asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes.pipeline import router as pipeline_router
from api.routes.leads import router as leads_router
from api.routes.prompts import router as prompts_router
from api.routes.analytics import router as analytics_router
from storage.database import init_db
from config.settings import settings

nest_asyncio.apply()

app = FastAPI(title="Lead Gen Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()
    
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from core.inbox_scanner import InboxScanner
    from core.follow_up_engine import FollowUpEngine
    
    scheduler = AsyncIOScheduler()
    
    # Run inbox scanner every 1 hour
    scanner = InboxScanner()
    scheduler.add_job(scanner.scan_for_replies, 'interval', hours=1)
    
    # Run follow up engine every day
    follow_up_engine = FollowUpEngine()
    scheduler.add_job(follow_up_engine.run_daily_followups, 'interval', days=1)
    
    scheduler.start()
    print("[SYSTEM] APScheduler started for background jobs (Inbox Sync & Follow-ups).")

@app.get("/api/debug")
async def debug_info():
    return {"model": settings.DEFAULT_LLM_MODEL}

app.include_router(pipeline_router, prefix="/api/pipeline", tags=["Pipeline"])
app.include_router(leads_router, prefix="/api/leads", tags=["Leads"])
app.include_router(prompts_router, prefix="/api/prompts", tags=["Prompts"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])

# Serve frontend static files if they exist (for production build)
frontend_path = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    
    # Catch-all route to serve index.html for React Router
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            from fastapi.responses import FileResponse
            return FileResponse(index_path)
        return {"error": "Frontend not built yet"}

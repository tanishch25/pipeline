from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from main import run_pipeline_async, global_state
import asyncio

router = APIRouter()

# Simple in-memory channel for SSE logs
# In production, use Redis pub/sub. Here we just use an asyncio Queue.
log_queue = asyncio.Queue()

class PipelineRunRequest(BaseModel):
    query: str
    limit: int = 5
    mock_mode: bool = False
    engine: str = "hybrid"
    auto_send: bool = False

import traceback

async def generator_wrapper(query: str, limit: int, mock_mode: bool, engine: str, auto_send: bool):
    try:
        async for msg in run_pipeline_async(query, limit, mock_mode, engine, auto_send):
            await log_queue.put(msg)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Pipeline error:\n{error_trace}")
        await log_queue.put(f"Error: {str(e)}")
        for line in error_trace.split('\n'):
            await log_queue.put(line)
    finally:
        await log_queue.put("DONE")

@router.post("/stop")
async def stop_pipeline():
    global_state["should_stop"] = True
    return {"message": "Stop signal sent"}

@router.post("/run")
async def trigger_pipeline(req: PipelineRunRequest):
    global_state["should_stop"] = False
    # Clear the queue for the new run
    while not log_queue.empty():
        log_queue.get_nowait()
        
    asyncio.create_task(generator_wrapper(req.query, req.limit, req.mock_mode, req.engine, req.auto_send))
    return {"message": "Pipeline started"}

@router.get("/progress")
async def progress_stream(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                # Wait for the next message, with timeout to detect disconnects
                msg = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                yield {"data": msg}
                if msg == "DONE":
                    break
            except asyncio.TimeoutError:
                pass
    return EventSourceResponse(event_generator())

@router.post("/sync")
async def trigger_inbox_sync():
    from core.inbox_scanner import InboxScanner
    scanner = InboxScanner()
    asyncio.create_task(scanner.scan_for_replies())
    return {"message": "Inbox sync started in the background"}

@router.post("/followup")
async def trigger_followup():
    from core.follow_up_engine import FollowUpEngine
    engine = FollowUpEngine()
    asyncio.create_task(engine.run_daily_followups())
    return {"message": "Follow-up engine started in the background"}

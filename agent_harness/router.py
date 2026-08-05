import asyncio
import uuid
import json
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from .events import get_bus
from .state import create_state
from .execution_logger import create_table_if_missing, persist_event
from .workflows import dummy_graph

router = APIRouter(prefix="/agent", tags=["agent_harness"]) 

# Ensure execution DB exists
create_table_if_missing()

bus = get_bus()


@router.post("/execute")
async def execute(payload: dict, background_tasks: BackgroundTasks):
    """Start an execution and return execution_id. Events stream on /agent/events/{id}"""
    execution_id = uuid.uuid4().hex
    create_state(execution_id, workflow=payload.get("workflow", "dummy"), meta=payload)

    # Background task to run the workflow
    async def _runner():
        try:
            # publish initial event
            evt = {"event_id": uuid.uuid4().hex, "execution_id": execution_id, "type": "execution.start", "timestamp": asyncio.get_event_loop().time(), "meta": {"payload": {k: str(v)[:200] for k,v in payload.items()}}}
            await bus.publish(execution_id, evt)
            await persist_event(evt)

            res = await dummy_graph.run_workflow(execution_id, payload)

            final = {"event_id": uuid.uuid4().hex, "execution_id": execution_id, "type": "execution.finished", "timestamp": asyncio.get_event_loop().time(), "result": str(res)[:1000]}
            await bus.publish(execution_id, final)
            await persist_event(final)
        except Exception as e:
            err = {"event_id": uuid.uuid4().hex, "execution_id": execution_id, "type": "execution.error", "timestamp": asyncio.get_event_loop().time(), "meta": {"error": str(e)[:1000]}}
            await bus.publish(execution_id, err)
            await persist_event(err)

    # Schedule background runner
    loop = asyncio.get_event_loop()
    loop.create_task(_runner())

    return JSONResponse({"execution_id": execution_id})


@router.get("/events/{execution_id}")
async def events_stream(execution_id: str):
    """SSE endpoint — stream events for the provided execution_id

    Note: single-process SSE — subscribers are served from in-memory queues.
    """
    sub_id, q = await bus.subscribe(execution_id)

    async def event_generator():
        try:
            while True:
                evt = await q.get()
                # ensure it's JSON-serializable and small
                data = json.dumps(evt, default=str)
                yield f"data: {data}\n\n"
                # persist was already handled by publishers, but keep here optional
        except asyncio.CancelledError:
            return
        finally:
            await bus.unsubscribe(execution_id, sub_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

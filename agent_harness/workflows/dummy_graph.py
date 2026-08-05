import asyncio
import time
import uuid
from ..events import get_bus
from ..tracer import trace_execution

bus = get_bus()


async def _sleep_and_return(execution_id: str, delay: float = 0.2):
    await asyncio.sleep(delay)
    return {"status": "ok", "info": f"slept {delay}s"}


@trace_execution(name="dummy_work", node="CallBusinessFunction")
async def business_function(execution_id: str, payload: dict):
    # Simulate calling existing business logic; in Phase 2.1 keep it simple
    return await _sleep_and_return(execution_id, delay=0.3)


async def run_workflow(execution_id: str, payload: dict):
    t0 = time.time()
    # Request received
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "request.received", "timestamp": time.time(), "message": "Request received"})

    # Detect intent
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "node.start", "node": "DetectIntent", "timestamp": time.time()})
    await asyncio.sleep(0.05)
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "node.end", "node": "DetectIntent", "timestamp": time.time(), "status": "success"})

    # Selected workflow
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "workflow.selected", "workflow": "dummy", "timestamp": time.time()})

    # Build context
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "node.start", "node": "BuildContext", "timestamp": time.time()})
    await asyncio.sleep(0.03)
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "node.end", "node": "BuildContext", "timestamp": time.time(), "status": "success"})

    # Call business function (traced)
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "node.start", "node": "CallBusinessFunction", "timestamp": time.time()})
    res = await business_function(execution_id=execution_id, payload=payload)
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "node.end", "node": "CallBusinessFunction", "timestamp": time.time(), "status": "success", "output_summary": str(res)[:200]})

    # Validate
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "node.start", "node": "ValidateOutput", "timestamp": time.time()})
    await asyncio.sleep(0.02)
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "node.end", "node": "ValidateOutput", "timestamp": time.time(), "status": "success"})

    # Completed
    await bus.publish(execution_id, {"event_id": uuid.uuid4().hex, "type": "completed", "timestamp": time.time(), "duration_ms": (time.time()-t0)*1000.0, "result": res})

    return res

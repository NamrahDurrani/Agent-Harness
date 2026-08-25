import time
import functools
import inspect
import uuid
import asyncio
from typing import Callable, Any

from .events import get_bus
from .execution_logger import persist_event

bus = get_bus()


def _now():
    return time.time()


def trace_execution(name: str = None, node: str = None):
    """Decorator that emits function start/end events to the EventBus and persists them.

    Works with sync and async functions.
    """
    def _decorator(func: Callable):
        fname = name or func.__name__

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def _wrapped(*args, **kwargs):
                event_id = uuid.uuid4().hex
                start_ts = _now()
                start_evt = {
                    "event_id": event_id,
                    "type": "function.start",
                    "function_name": fname,
                    "node": node,
                    "timestamp": start_ts,
                    "status": "running",
                }
                await bus.publish(kwargs.get("execution_id") or (args[0] if args else ""), start_evt)
                await persist_event(start_evt)
                try:
                    result = await func(*args, **kwargs)
                    end_ts = _now()
                    dur = (end_ts - start_ts) * 1000.0
                    end_evt = {
                        "event_id": event_id,
                        "type": "function.end",
                        "function_name": fname,
                        "node": node,
                        "timestamp": end_ts,
                        "duration_ms": dur,
                        "status": "success",
                        "output_summary": str(result)[:1000],
                    }
                    await bus.publish(kwargs.get("execution_id") or (args[0] if args else ""), end_evt)
                    await persist_event(end_evt)
                    return result
                except Exception as e:
                    end_ts = _now()
                    dur = (end_ts - start_ts) * 1000.0
                    err_evt = {
                        "event_id": event_id,
                        "type": "function.error",
                        "function_name": fname,
                        "node": node,
                        "timestamp": end_ts,
                        "duration_ms": dur,
                        "status": "error",
                        "meta": {"error_type": type(e).__name__, "error_message": str(e)[:1000]},
                    }
                    await bus.publish(kwargs.get("execution_id") or (args[0] if args else ""), err_evt)
                    await persist_event(err_evt)
                    raise
            return _wrapped
        else:
            @functools.wraps(func)
            def _wrapped(*args, **kwargs):
                # sync wrapper runs blocking; publish via asyncio
                # FIX: asyncio.get_event_loop() raises RuntimeError (Python
                # 3.10+, especially 3.12/3.13) when called from a worker
                # thread that never had a loop set — e.g. an
                # asyncio.to_thread() executor thread. Every loop.create_task
                # call below this point already tolerates failure via
                # try/except; this one line wasn't guarded the same way, so
                # a decorated sync function called from such a thread (e.g.
                # mcp_generate_pdf via the PDF export workflow) would crash
                # before ever running the actual function. Tracing becomes a
                # best-effort no-op here instead — the caller (e.g.
                # run_report_workflow) already emits its own start/end/error
                # events on the correctly-captured main loop, so no
                # visibility is actually lost.
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = None
                event_id = uuid.uuid4().hex
                start_ts = _now()
                start_evt = {
                    "event_id": event_id,
                    "type": "function.start",
                    "function_name": fname,
                    "node": node,
                    "timestamp": start_ts,
                    "status": "running",
                }
                try:
                    loop.create_task(bus.publish(kwargs.get("execution_id") or (args[0] if args else ""), start_evt))
                    loop.create_task(persist_event(start_evt))
                except Exception:
                    pass
                try:
                    result = func(*args, **kwargs)
                    end_ts = _now()
                    dur = (end_ts - start_ts) * 1000.0
                    end_evt = {
                        "event_id": event_id,
                        "type": "function.end",
                        "function_name": fname,
                        "node": node,
                        "timestamp": end_ts,
                        "duration_ms": dur,
                        "status": "success",
                        "output_summary": str(result)[:1000],
                    }
                    try:
                        loop.create_task(bus.publish(kwargs.get("execution_id") or (args[0] if args else ""), end_evt))
                        loop.create_task(persist_event(end_evt))
                    except Exception:
                        pass
                    return result
                except Exception as e:
                    end_ts = _now()
                    dur = (end_ts - start_ts) * 1000.0
                    err_evt = {
                        "event_id": event_id,
                        "type": "function.error",
                        "function_name": fname,
                        "node": node,
                        "timestamp": end_ts,
                        "duration_ms": dur,
                        "status": "error",
                        "meta": {"error_type": type(e).__name__, "error_message": str(e)[:1000]},
                    }
                    try:
                        loop.create_task(bus.publish(kwargs.get("execution_id") or (args[0] if args else ""), err_evt))
                        loop.create_task(persist_event(err_evt))
                    except Exception:
                        pass
                    raise
            return _wrapped

    return _decorator
import asyncio
import uuid
from typing import Dict, Any

# Simple in-memory event bus for single-process SSE
class EventBus:
    def __init__(self):
        # execution_id -> dict[sub_id -> asyncio.Queue]
        self._subs: Dict[str, Dict[str, asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, execution_id: str, event: Dict[str, Any]):
        async with self._lock:
            subs = self._subs.get(execution_id, {})
            for q in list(subs.values()):
                # put_nowait to avoid blocking publisher; consumers should drain
                try:
                    q.put_nowait(event)
                except Exception:
                    pass

    async def subscribe(self, execution_id: str):
        q = asyncio.Queue()
        sub_id = uuid.uuid4().hex
        async with self._lock:
            bucket = self._subs.setdefault(execution_id, {})
            bucket[sub_id] = q
        return sub_id, q

    async def unsubscribe(self, execution_id: str, sub_id: str):
        async with self._lock:
            bucket = self._subs.get(execution_id)
            if not bucket:
                return
            bucket.pop(sub_id, None)
            if not bucket:
                self._subs.pop(execution_id, None)


# Singleton bus
_bus: EventBus = EventBus()


def get_bus() -> EventBus:
    return _bus

import asyncio
import uuid
from agent_harness.events import get_bus
from agent_harness.workflows.dummy_graph import run_workflow

async def main():
    execution_id = uuid.uuid4().hex
    bus = get_bus()
    sub_id, q = await bus.subscribe(execution_id)

    async def runner():
        await run_workflow(execution_id, {"workflow": "dummy", "args": {}})

    task = asyncio.create_task(runner())

    try:
        while True:
            evt = await q.get()
            print('EVT:', evt)
            if evt.get('type') == 'completed' or evt.get('type') == 'execution.finished':
                break
    finally:
        await bus.unsubscribe(execution_id, sub_id)

asyncio.run(main())

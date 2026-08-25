"""
agent_harness/code_narration.py

Wraps a document-generation handler so the ACTUAL code it runs (report
generation, chart rendering, PDF layout) gets emitted as a harness event
before execution — this is what the frontend renders as the collapsible
"Analyzing / Python" block, not a separate fake code generator. We show
the real code, not a summary of it, so "View Analysis" stays honest.

Event contract addition (additive to agent_box.py's existing
request.received / agent.* / tool.* / validation.* / artifact.created /
completed / execution.error stream):

    {"type": "code.block", "event": "code.block",
     "parent_agent_id": <agent id this code ran under>,
     "meta": {"label": <str>, "language": "python", "code": <str>}}

AgriBot.jsx's SSE handler listens for this exact shape.
"""
import inspect
from typing import Any, Callable


async def run_with_code_narration(harness, parent_agent_id: str, label: str,
                                    fn: Callable, *args, **kwargs) -> Any:
    """
    harness: the AgentHarness instance already in scope in the calling
        capability handler (agent_box.AgentHarness) — same instance,
        no new one created.
    parent_agent_id: the agent id this code block should nest under in
        the Agent Execution tree (the same id already passed into the
        handler as `parent_agent_id`).
    label: shown as the collapsible block's header, e.g.
        "Rendering document", "Generating chart".
    fn: the actual async function that does the work — its real
        `inspect.getsource()` is what gets shown, not a paraphrase.
    """
    try:
        source = inspect.getsource(fn)
    except (OSError, TypeError):
        source = f"# {getattr(fn, '__name__', 'handler')} (source unavailable at runtime)"

    await harness._emit({
        "type": "code.block", "event": "code.block",
        "parent_agent_id": parent_agent_id,
        "meta": {"label": label, "language": "python", "code": source},
    })
    return await fn(*args, **kwargs)

"""
agent_harness/langgraph_agent.py

EXPERIMENTAL / ALTERNATIVE ORCHESTRATION — kept alongside the native
asyncio Dynamic Harness (dynamic_harness.py) for future comparison, per
project decision. Not on the current production path.

The core LangGraph agent/tool loop:

    START -> agent_node -> (tool_node -> agent_node)* -> validate_node -> END

WHY A MANUAL ReAct LOOP INSTEAD OF LangGraph's prebuilt tool-calling
agent / a ChatModel's native .bind_tools(): the project's existing
LLMClient (rag_pipeline.py) is a thin wrapper around Groq/Ollama/qwen
that exposes `.call(system_prompt, user_prompt, max_tokens, temperature,
model)` — not a LangChain BaseChatModel. Rather than adding a new
langchain-groq dependency and a second LLM client alongside the one
already used everywhere else, agent_node() prompts the SAME LLMClient
with a strict JSON-only instruction and parses the result. LangGraph
still owns the actual state machine / control flow / checkpointing
(StateGraph below) — only the "ask the model what to do next" step is
hand-rolled instead of using a framework-native tool-calling model.
"""
import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END

from .agent_box import AgentHarness
from .langgraph_state import AutonomousAgentState, new_state
from .tools import ToolContext

# NOTE: TOOL_REGISTRY / format_tool_manifest_for_prompt used to live in
# tools.py but were removed when tools.py was refactored for the native
# Dynamic Harness (default_capabilities.py owns capability wiring now).
# This experimental LangGraph path needs its own lightweight tool
# manifest — rebuilt here from default_capabilities.py's registry so it
# doesn't silently drift from what capabilities actually exist.
from .default_capabilities import build_default_registry

_REGISTRY = build_default_registry()


def _tool_manifest() -> str:
    return _REGISTRY.manifest_for_prompt()


def _tool_names() -> List[str]:
    return [c.name for c in _REGISTRY.all()]


@dataclass
class ExecutionLimits:
    max_iterations: int = 15
    max_tool_calls: int = 25
    max_tool_retries: int = 3
    max_self_corrections: int = 2


DEFAULT_LIMITS = ExecutionLimits()

_SYSTEM_TEMPLATE = """{role}

MISSION: Complete the user's requested goal accurately using only the tools listed below.
Do not fabricate information a tool would provide — call the tool instead.
Only use tools that are actually necessary for this specific goal; do not call a tool "just in case".

AVAILABLE TOOLS:
{tool_manifest}

RULES:
- If you still need information or an action to complete the goal, respond with ONLY this JSON, nothing else:
  {{"tool": "<tool_name>", "args": {{...}}}}
- If you have enough information to fully answer the goal, respond with ONLY this JSON, nothing else:
  {{"final_answer": "<your complete answer, citing sources by name where you used search_agriculture_knowledge or search_uploaded_documents>"}}
- If completing the goal genuinely requires information only the user can give you (e.g. a location, a crop
  name, a missing file), and no tool can supply it, respond with ONLY this JSON, nothing else:
  {{"ask_user": "<one specific question>"}}
- Never invent a tool name that isn't listed above.
- Never emit both a tool call and a final answer in the same response.
- Do not include any text outside the single JSON object.

RECOVERY: if an observation says a tool FAILED, do not call that exact same tool with the exact same
args again. Instead: try different/corrected args, try a different tool that could get the same
information another way, or — only if nothing above can work — ask_user. If retrieve_memory has
relevant saved facts (a location, a preference) from an earlier turn, prefer using them over asking
the user again.
"""

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_BLOCK_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _render_messages(messages: List[Dict[str, str]]) -> str:
    lines = []
    for m in messages:
        lines.append(f"[{m['role'].upper()}] {m['content']}")
    return "\n".join(lines)


class AutonomousAgentRunner:
    def __init__(self, llm, harness: AgentHarness, root_agent_id: str,
                 tool_ctx: ToolContext, limits: ExecutionLimits = DEFAULT_LIMITS):
        self.llm = llm
        self.harness = harness
        self.root_agent_id = root_agent_id
        self.tool_ctx = tool_ctx
        self.limits = limits
        self._self_corrections = 0

    async def agent_node(self, state: AutonomousAgentState) -> Dict[str, Any]:
        iteration = state.get("iteration_count", 0) + 1

        if iteration > self.limits.max_iterations:
            return {
                "iteration_count": iteration,
                "status": "failed",
                "final_answer": state.get("final_answer") or
                    "I wasn't able to finish within the allotted number of steps.",
                "errors": state.get("errors", []) + [
                    {"stage": "agent_node", "error": "max_iterations exceeded"}],
            }

        system_prompt = _SYSTEM_TEMPLATE.format(role=state["role"], tool_manifest=_tool_manifest())
        user_prompt = (
            f"GOAL: {state['goal']}\n\n"
            f"CONVERSATION / OBSERVATIONS SO FAR:\n{_render_messages(state['messages'])}\n\n"
            "What do you do next? Respond with ONLY the JSON object described in the rules."
        )

        raw, _usage = await asyncio.to_thread(
            self.llm.call, system_prompt, user_prompt, 700, 0.1, None)
        parsed = _extract_json(raw)

        if parsed is None:
            return {
                "iteration_count": iteration,
                "status": "completed",
                "final_answer": raw.strip(),
                "messages": state["messages"] + [{"role": "assistant", "content": raw}],
            }

        if "final_answer" in parsed:
            return {
                "iteration_count": iteration,
                "pending_tool_calls": [],
                "final_answer": parsed["final_answer"],
                "messages": state["messages"] + [{"role": "assistant", "content": raw}],
            }

        if "ask_user" in parsed:
            return {
                "iteration_count": iteration,
                "pending_tool_calls": [],
                "status": "waiting_for_user",
                "final_answer": parsed["ask_user"],
                "messages": state["messages"] + [{"role": "assistant", "content": raw}],
            }

        tool_name = parsed.get("tool")
        args = parsed.get("args", {}) or {}
        if tool_name not in _tool_names():
            observation = f"ERROR: '{tool_name}' is not an available tool. Choose from the AVAILABLE TOOLS list."
            return {
                "iteration_count": iteration,
                "pending_tool_calls": [],
                "messages": state["messages"] + [
                    {"role": "assistant", "content": raw},
                    {"role": "tool", "content": observation},
                ],
            }

        call = {"call_id": f"c{iteration}", "tool": tool_name, "args": args}
        return {
            "iteration_count": iteration,
            "pending_tool_calls": [call],
            "messages": state["messages"] + [{"role": "assistant", "content": raw}],
        }

    async def tool_node(self, state: AutonomousAgentState) -> Dict[str, Any]:
        calls = state.get("pending_tool_calls", [])
        tool_call_count = state.get("tool_call_count", 0)
        new_messages = list(state["messages"])
        new_results = list(state.get("tool_results", []))
        new_sources = list(state.get("sources", []))
        new_artifacts = list(state.get("artifacts", []))
        errors = list(state.get("errors", []))

        for call in calls:
            if tool_call_count >= self.limits.max_tool_calls:
                new_messages.append({
                    "role": "tool",
                    "content": "ERROR: tool-call limit reached for this request. "
                               "Summarize what you have and finish now.",
                })
                errors.append({"stage": "tool_node", "error": "max_tool_calls exceeded"})
                continue

            tool_call_count += 1
            cap = _REGISTRY.get(call["tool"])

            async def _invoke():
                return await cap.handler(
                    self.tool_ctx, harness=self.harness,
                    parent_agent_id=self.root_agent_id, **call["args"])

            try:
                result = await self.harness.run_tool(
                    cap.agent_name, lambda: _invoke(),
                    parent_agent_id=self.root_agent_id,
                    input_summary=call["args"],
                    max_retries=self.limits.max_tool_retries,
                )
                output = result.output if hasattr(result, "output") else result
                ok, error = (result.status == "success") if hasattr(result, "status") else True, None
            except Exception as e:
                output, ok, error = None, False, str(e)
                errors.append({"stage": "tool_node", "tool": call["tool"], "error": error})

            new_results.append({
                "call_id": call["call_id"], "tool": call["tool"],
                "ok": ok, "output": output, "error": error,
            })

            if ok and isinstance(output, dict):
                if output.get("sources"):
                    new_sources.extend(output["sources"])
                if call["tool"] == "pdf_generate" and output.get("filename"):
                    new_artifacts.append({"type": "pdf", "ref": output["filename"]})
                    await self.harness.artifact_created("pdf", output["filename"],
                                                         parent_agent_id=self.root_agent_id)

            observation = f"Result of {call['tool']}: " + (
                json.dumps(output, default=str)[:1500] if ok else f"FAILED — {error}")
            new_messages.append({"role": "tool", "content": observation})

        return {
            "pending_tool_calls": [],
            "tool_calls": state.get("tool_calls", []) + calls,
            "tool_results": new_results,
            "tool_call_count": tool_call_count,
            "messages": new_messages,
            "sources": new_sources,
            "artifacts": new_artifacts,
            "errors": errors,
        }

    async def validate_node(self, state: AutonomousAgentState) -> Dict[str, Any]:
        vid = await self.harness.validation_start(
            "FinalAnswerValidation", parent_agent_id=self.root_agent_id,
            input_summary={"has_sources": bool(state.get("sources"))})

        used_evidence_tool = any(
            r["tool"] in ("agriculture_rag", "document_search")
            for r in state.get("tool_results", []))
        has_sources = bool(state.get("sources"))
        made_pdf = any(r["tool"] == "pdf_generate" and r["ok"] for r in state.get("tool_results", []))
        pdf_validated = any(r["tool"] == "pdf_validate" and isinstance(r.get("output"), dict)
                             and r["output"].get("ok") for r in state.get("tool_results", []))

        checks = {
            "has_final_answer": bool(state.get("final_answer")),
            "sources_present_if_evidence_used": (not used_evidence_tool) or has_sources,
            "pdf_validated_if_created": (not made_pdf) or pdf_validated,
        }
        passed = all(checks.values())

        await self.harness.validation_end(vid, "FinalAnswerValidation", passed,
                                           detail=checks, parent_agent_id=self.root_agent_id)

        if passed:
            return {"status": "completed", "validation_results": checks}

        self._self_corrections += 1
        if self._self_corrections > self.limits.max_self_corrections:
            return {"status": "completed", "validation_results": checks,
                    "final_answer": state.get("final_answer")}

        missing = [k for k, v in checks.items() if not v]
        return {
            "status": "running",
            "pending_tool_calls": [],
            "final_answer": None,
            "validation_results": checks,
            "messages": state["messages"] + [
                {"role": "tool", "content": f"VALIDATION FAILED: {missing}. Fix this before finishing."}],
        }


def _route_after_agent(state: AutonomousAgentState) -> str:
    if state.get("status") in ("failed", "waiting_for_user"):
        return "end"
    if state.get("pending_tool_calls"):
        return "tool"
    return "validate"


def _route_after_validate(state: AutonomousAgentState) -> str:
    return "end" if state.get("status") == "completed" else "agent"


def build_graph(runner: AutonomousAgentRunner):
    graph = StateGraph(AutonomousAgentState)
    graph.add_node("agent", runner.agent_node)
    graph.add_node("tool", runner.tool_node)
    graph.add_node("validate", runner.validate_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", _route_after_agent,
                                 {"tool": "tool", "validate": "validate", "end": END})
    graph.add_edge("tool", "agent")
    graph.add_conditional_edges("validate", _route_after_validate,
                                 {"agent": "agent", "end": END})
    return graph.compile()


async def run_autonomous_agent(
    execution_id: str, session_id: str, user_query: str,
    llm, harness: AgentHarness, root_agent_id: str, tool_ctx: ToolContext,
    limits: ExecutionLimits = DEFAULT_LIMITS,
    uploaded_files: Optional[List[Dict[str, Any]]] = None,
) -> AutonomousAgentState:
    runner = AutonomousAgentRunner(llm, harness, root_agent_id, tool_ctx, limits)
    app = build_graph(runner)
    init = new_state(execution_id, session_id, user_query, uploaded_files=uploaded_files)
    final_state = await app.ainvoke(init, config={"recursion_limit": limits.max_iterations * 4})
    return final_state
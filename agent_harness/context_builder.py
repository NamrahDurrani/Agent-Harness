from typing import Dict, Any, List

# Minimal context builder stubs — these will be expanded per workflow.

def build_pdf_context(conversation: List[Dict[str, Any]], pdf_template: Dict[str, Any]) -> Dict[str, Any]:
    # Only include conversation and template
    convo_trimmed = conversation[-6:]
    return {
        "conversation": convo_trimmed,
        "pdf_template": {k: pdf_template.get(k) for k in ("title", "author") if k in pdf_template}
    }


def build_rag_context(conversation: List[Dict[str, Any]], retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "conversation": conversation[-6:],
        "retrieved_chunks": retrieved_chunks[:8]
    }


def build_weather_context(conversation: List[Dict[str, Any]], weather_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "conversation": conversation[-6:],
        "weather": {"summary": weather_result.get("summary"), "temp": weather_result.get("temp")}
    }

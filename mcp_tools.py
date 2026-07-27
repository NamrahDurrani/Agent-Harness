"""
mcp_tools.py
============
MCP (Model Context Protocol) tool integrations for the Agentic RAG pipeline.

What MCP does here
------------------
MCP lets the RAG pipeline call *external tools* (weather APIs, crop databases,
government portals, calculators) through a standardised JSON-RPC interface,
without hardcoding each integration.  The LLM (Groq/Llama) decides *which*
tool to call based on the user query; this module executes the call and returns
structured results that feed back into the context before generation.

Architecture
------------
    User Query
        │
        ▼
    Orchestrator (LLM)
        │   ← sees tool_manifest (list of available MCP tools)
        ▼
    Tool selection  ←─ if orchestrator returns {"tool": "weather", ...}
        │
        ▼
    mcp_tools.dispatch(tool_name, params)
        │
        ▼
    Tool result injected into RAG context
        │
        ▼
    Main LLM generation (grounded answer)

Included tools
--------------
  weather          — Open-Meteo (free, no key) current + 7-day forecast
  crop_calendar    — Rule-based Pakistan crop sowing/harvest calendar
  unit_converter   — Acres↔hectares, kg/acre↔ton/ha, etc.
  tavily_search    — Live web search (requires TAVILY_API_KEY)
  docling_ingest   — PDF → structured text via Docling (for MCP doc ingestion)

Adding a new tool
-----------------
1. Write a function  def _tool_<name>(params: dict) -> dict
2. Register it in  TOOL_REGISTRY  below
3. Add its schema to  TOOL_MANIFEST

The orchestrator prompt in rag_pipeline.py already reads TOOL_MANIFEST and
will automatically offer the new tool to the LLM.
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
#  Tool implementations
# ═══════════════════════════════════════════════════════════════════════════════

# ── 1. Weather (Open-Meteo — free, no API key required) ──────────────────────

def _tool_weather(params: Dict) -> Dict:
    """
    Get current weather + 7-day forecast for a location.
    Uses Open-Meteo (https://open-meteo.com) — completely free, no key.

    params:
        location (str): city or district name, e.g. "Lahore", "Multan"
        lat      (float, optional): latitude  — used if provided, skips geocoding
        lon      (float, optional): longitude
    """
    import urllib.request

    location = params.get("location", "Lahore")
    lat = params.get("lat")
    lon = params.get("lon")

    # Step 1: geocode if lat/lon not given
    if lat is None or lon is None:
        geo_url = (
            f"https://geocoding-api.open-meteo.com/v1/search"
            f"?name={urllib.parse.quote(location)}&count=1&language=en&format=json"
        )
        try:
            import urllib.parse
            with urllib.request.urlopen(geo_url, timeout=5) as resp:
                geo = json.loads(resp.read())
            result = geo.get("results", [{}])[0]
            lat = result.get("latitude", 31.5497)   # default Lahore
            lon = result.get("longitude", 74.3436)
            location = result.get("name", location)
        except Exception as e:
            lat, lon = 31.5497, 74.3436
            print(f"  [MCP/weather] Geocoding failed ({e}), using Lahore coords")

    # Step 2: fetch weather
    wx_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weathercode"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
        f"&timezone=Asia%2FKarachi&forecast_days=7"
    )
    try:
        with urllib.request.urlopen(wx_url, timeout=8) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"error": f"Weather fetch failed: {e}"}

    current = data.get("current", {})
    daily   = data.get("daily", {})

    def wcode_label(code: int) -> str:
        mapping = {0:"Clear sky", 1:"Mainly clear", 2:"Partly cloudy", 3:"Overcast",
                   45:"Foggy", 48:"Icy fog", 51:"Light drizzle", 53:"Moderate drizzle",
                   55:"Heavy drizzle", 61:"Slight rain", 63:"Moderate rain", 65:"Heavy rain",
                   71:"Slight snow", 73:"Moderate snow", 75:"Heavy snow",
                   80:"Rain showers", 81:"Heavy showers", 95:"Thunderstorm"}
        return mapping.get(code, f"Code {code}")

    forecast_days = []
    dates = daily.get("time", [])
    for i, d in enumerate(dates):
        forecast_days.append({
            "date":      d,
            "max_c":     daily["temperature_2m_max"][i],
            "min_c":     daily["temperature_2m_min"][i],
            "rain_mm":   daily["precipitation_sum"][i],
            "condition": wcode_label(daily["weathercode"][i]),
        })

    return {
        "location":     location,
        "lat":          lat,
        "lon":          lon,
        "current": {
            "temp_c":    current.get("temperature_2m"),
            "humidity":  current.get("relative_humidity_2m"),
            "wind_kph":  current.get("wind_speed_10m"),
            "rain_mm":   current.get("precipitation"),
            "condition": wcode_label(current.get("weathercode", 0)),
        },
        "forecast_7d":  forecast_days,
    }


# ── 2. Pakistan Crop Calendar ─────────────────────────────────────────────────

_CROP_CALENDAR = {
    "wheat": {
        "sowing":  "October–November",
        "harvest": "April–May",
        "regions": "Punjab, Sindh, KPK",
        "notes":   "Rabi (winter) crop. Optimal sowing Nov 1–15 in Punjab.",
    },
    "cotton": {
        "sowing":  "April–May",
        "harvest": "September–November",
        "regions": "Punjab (central), Sindh",
        "notes":   "Kharif (summer) crop. Requires min 25°C for germination.",
    },
    "rice": {
        "sowing":  "June–July (transplant)",
        "harvest": "October–November",
        "regions": "Punjab (Sheikhupura, Gujranwala), Sindh",
        "notes":   "Basmati in Punjab; IRRI varieties in Sindh.",
    },
    "sugarcane": {
        "sowing":  "February–March (spring), October (autumn)",
        "harvest": "November–April",
        "regions": "Punjab, Sindh, KPK",
        "notes":   "Perennial; ratoon crop possible for 2-3 seasons.",
    },
    "maize": {
        "sowing":  "April–May (kharif), January–February (rabi)",
        "harvest": "August–September (kharif), May–June (rabi)",
        "regions": "KPK, Punjab",
        "notes":   "Hybrid varieties gaining in Punjab plains.",
    },
    "sunflower": {
        "sowing":  "February–March",
        "harvest": "June–July",
        "regions": "Punjab, Sindh",
        "notes":   "Spring crop; drought-tolerant once established.",
    },
}

def _tool_crop_calendar(params: Dict) -> Dict:
    """
    Return Pakistan crop calendar for a named crop.
    params:  { "crop": "wheat" }
    """
    crop = params.get("crop", "").lower().strip()
    if crop in _CROP_CALENDAR:
        return {"crop": crop, **_CROP_CALENDAR[crop]}
    # fuzzy match
    matches = [k for k in _CROP_CALENDAR if crop in k or k in crop]
    if matches:
        return {"crop": matches[0], **_CROP_CALENDAR[matches[0]]}
    return {
        "error":       f"Crop '{crop}' not in calendar.",
        "available":   list(_CROP_CALENDAR.keys()),
    }


# ── 3. Unit Converter ─────────────────────────────────────────────────────────

def _tool_unit_converter(params: Dict) -> Dict:
    """
    Convert agricultural units.
    params:  { "value": 10, "from_unit": "acres", "to_unit": "hectares" }
    Supported: acres↔hectares, kg↔tons, kg/acre↔ton/ha, mm↔inches, °C↔°F
    """
    value     = float(params.get("value", 1))
    from_unit = params.get("from_unit", "").lower().replace(" ", "")
    to_unit   = params.get("to_unit",   "").lower().replace(" ", "")

    CONVERSIONS = {
        ("acres",     "hectares"):  lambda v: v * 0.404686,
        ("hectares",  "acres"):     lambda v: v * 2.47105,
        ("kg",        "tons"):      lambda v: v / 1000,
        ("tons",      "kg"):        lambda v: v * 1000,
        ("kg/acre",   "ton/ha"):    lambda v: v * 0.001 / 0.404686 * 1000,
        ("ton/ha",    "kg/acre"):   lambda v: v * 1000 * 0.404686 / 1000,
        ("mm",        "inches"):    lambda v: v / 25.4,
        ("inches",    "mm"):        lambda v: v * 25.4,
        ("°c",        "°f"):        lambda v: v * 9/5 + 32,
        ("°f",        "°c"):        lambda v: (v - 32) * 5/9,
    }

    key = (from_unit, to_unit)
    if key in CONVERSIONS:
        result = CONVERSIONS[key](value)
        return {
            "input":  f"{value} {from_unit}",
            "output": f"{round(result, 4)} {to_unit}",
            "factor": round(result / value, 6) if value != 0 else None,
        }
    return {
        "error": f"Conversion from '{from_unit}' to '{to_unit}' not supported.",
        "supported_conversions": [f"{a} → {b}" for a, b in CONVERSIONS],
    }


# ── 4. Tavily live web search (wraps tavily_search.py) ───────────────────────

def _tool_tavily_search(params: Dict) -> Dict:
    """
    Live web search via Tavily.
    params:  { "query": "Ug99 rust resistance varieties Punjab 2025" }
    """
    try:
        from tavily_search import tavily_web_search, format_for_llm
        results = tavily_web_search(
            query=params.get("query", ""),
            max_results=params.get("max_results", 5),
        )
        return {
            "results":    results,
            "llm_context": format_for_llm(results),
            "count":      len(results),
        }
    except Exception as e:
        return {"error": str(e), "results": []}


# ── 5. Docling PDF ingestion ──────────────────────────────────────────────────

def _tool_docling_ingest(params: Dict) -> Dict:
    """
    Ingest a PDF using Docling for high-quality structured extraction.
    Docling handles:
      - Proper reading order (no column mixing)
      - Table extraction as Markdown
      - Figure/caption pairing
      - Scanned page OCR via EasyOCR

    params:
        file_path   (str): absolute path to the PDF
        project_id  (str, optional): associate chunks with a project
        scope       (str): "project" | "global"  (default "global")
        chunk_size  (int): chars per chunk (default 600)
        overlap     (int): overlap chars (default 100)

    Requires:  pip install docling
    """
    file_path  = params.get("file_path", "")
    project_id = params.get("project_id")
    scope      = params.get("scope", "global")
    chunk_size = int(params.get("chunk_size", 600))
    overlap    = int(params.get("overlap", 100))

    if not file_path:
        return {"error": "file_path is required"}

    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        return {
            "error": "Docling not installed. Run: pip install docling",
            "fallback": "Using PyMuPDF extraction instead (already installed)",
        }

    try:
        converter  = DocumentConverter()
        result     = converter.convert(file_path)
        doc        = result.document

        # Export to Markdown (preserves tables, headings, lists)
        full_text  = doc.export_to_markdown()

        # Chunk the markdown
        chunks = []
        start  = 0
        while start < len(full_text):
            end   = start + chunk_size
            chunk = full_text[start:end]
            chunks.append({
                "text":       chunk,
                "start_char": start,
                "source":     file_path,
                "scope":      scope,
                "project_id": project_id,
            })
            start += chunk_size - overlap

        return {
            "status":     "ok",
            "file":       file_path,
            "scope":      scope,
            "project_id": project_id,
            "num_chunks": len(chunks),
            "preview":    full_text[:300],
            "chunks":     chunks,          # caller adds these to ChromaDB
        }

    except Exception as e:
        return {"error": f"Docling ingestion failed: {e}"}


# ═══════════════════════════════════════════════════════════════════════════════
#  Tool registry + manifest
# ═══════════════════════════════════════════════════════════════════════════════

# ── 6. Weather Sowing Advisor (wraps mcp_weather_advisor.py) ─────────────────

def _tool_weather_sowing_advisor(params: Dict) -> Dict:
    """
    Agricultural weather + sowing advice.
    Answers: "Is tomorrow a good day for wheat sowing in Lahore?"

    params:
        location   (str): city name e.g. "Lahore", "Multan"
        crop       (str): crop name e.g. "wheat", "cotton", "rice"
        target_day (str): "today" | "tomorrow" | "Saturday" | "YYYY-MM-DD"
    """
    try:
        from mcp_weather_advisor import get_sowing_advice, format_for_llm
        location   = params.get("location", "Lahore")
        crop       = params.get("crop", "wheat")
        target_day = params.get("target_day", "tomorrow")
        result     = get_sowing_advice(location, crop, target_day)
        return {
            **result,
            "llm_context": format_for_llm(result),
        }
    except Exception as e:
        # Fall back to basic weather if advisor fails
        return _tool_weather({"location": params.get("location", "Lahore")})


TOOL_REGISTRY: Dict[str, callable] = {
    "weather":                  _tool_weather,
    "weather_sowing_advisor":   _tool_weather_sowing_advisor,
    "crop_calendar":            _tool_crop_calendar,
    "unit_converter":           _tool_unit_converter,
    "tavily_search":            _tool_tavily_search,
    "docling_ingest":           _tool_docling_ingest,
}

# This manifest is injected into the orchestrator system prompt so the LLM
# knows what tools are available and when to call them.
TOOL_MANIFEST: List[Dict] = [
    {
        "name":        "weather",
        "description": "Get current weather and 7-day forecast for any Pakistan city/district. "
                       "Use when user asks about weather, rain, temperature, or planting conditions.",
        "params":      {"location": "string (city name)", "lat": "optional float", "lon": "optional float"},
    },
    {
        "name":        "crop_calendar",
        "description": "Return Pakistan sowing and harvest calendar for a named crop. "
                       "Use when user asks 'when to sow wheat', 'cotton season', etc.",
        "params":      {"crop": "string e.g. wheat, cotton, rice, maize, sugarcane"},
    },
    {
        "name":        "unit_converter",
        "description": "Convert agricultural units: acres↔hectares, kg↔tons, mm↔inches, °C↔°F. "
                       "Use when user mentions unit conversions or asks 'how many X in Y'.",
        "params":      {"value": "number", "from_unit": "string", "to_unit": "string"},
    },
    # NOTE: tavily_search is intentionally NOT listed here. If it's in
    # TOOL_MANIFEST, the LLM orchestrator (_mcp_dispatch, called on EVERY
    # query) can proactively choose to search the web instead of using the
    # RAG index — this is exactly what produced random/off-topic web
    # results even after translation and retrieval were both fixed.
    # tavily_search stays in TOOL_REGISTRY below (dispatch() can still call
    # it by name) so rag_pipeline.py's _generate_from_web() fallback path
    # keeps working — that's the ONLY place it should ever be invoked from.
    {
        "name":        "weather_sowing_advisor",
        "description": "Get live weather forecast AND agricultural sowing advice for a crop + location. "
                       "Use when user asks 'is tomorrow good for sowing', 'weather for cotton', "
                       "'should I irrigate today', or any weather+agriculture combo question.",
        "params":      {
            "location":   "string — Pakistan city/district",
            "crop":       "string — wheat, cotton, rice, maize, sugarcane",
            "target_day": "today | tomorrow | Saturday | YYYY-MM-DD",
        },
    },
    {
        "name":        "docling_ingest",
        "description": "Ingest a PDF using Docling for high-quality table and text extraction. "
                       "Use this when a user uploads a new document that needs to be added to the knowledge base.",
        "params":      {
            "file_path":  "absolute path string",
            "project_id": "optional string",
            "scope":      "project | global",
        },
    },
]


def dispatch(tool_name: str, params: Dict) -> Dict:
    """
    Execute a tool by name and return its result dict.

    Usage in rag_pipeline.py:
        from mcp_tools import dispatch, TOOL_MANIFEST
        result = dispatch("weather", {"location": "Multan"})
    """
    fn = TOOL_REGISTRY.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool '{tool_name}'. Available: {list(TOOL_REGISTRY)}"}
    try:
        result = fn(params)
        print(f"  [MCP] Tool '{tool_name}' → {list(result.keys())}")
        return result
    except Exception as e:
        return {"error": f"Tool '{tool_name}' raised: {e}"}


def format_tool_manifest_for_prompt() -> str:
    """Return a compact string listing available tools, for the orchestrator prompt."""
    lines = ["Available MCP tools (call these by returning JSON {\"tool\": name, \"params\": {...}}):"]
    for t in TOOL_MANIFEST:
        param_str = ", ".join(f"{k}: {v}" for k, v in t["params"].items())
        lines.append(f"  • {t['name']}({param_str})\n    → {t['description']}")
    return "\n".join(lines)
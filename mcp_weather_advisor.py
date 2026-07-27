"""
mcp_weather_advisor.py
======================
MCP Tool: Live weather + agricultural sowing/activity advice.

Answers questions like:
  "Is tomorrow a good day for wheat sowing in Lahore?"
  "What is the weather forecast for Multan this week?"
  "Should I irrigate my cotton field in Faisalabad today?"

Architecture:
    User asks weather/sowing question
        → RAG pipeline detects weather intent (via orchestrator LLM)
        → calls mcp_tools.dispatch("weather", {"location": city})
        → THIS module's get_sowing_advice() wraps the raw weather data
          with crop-specific agricultural advice
        → structured advice injected into LLM context
        → LLM generates final grounded answer with [Web N] citations if available

APIs used:
    - Open-Meteo (https://open-meteo.com)  — FREE, no API key needed
    - Open-Meteo Geocoding API             — FREE, no API key needed

No pip install needed — uses only Python stdlib urllib.

Terminal test:
    python mcp_weather_advisor.py
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Optional, List


# ═══════════════════════════════════════════════════════════════════════════════
#  Weather code descriptions (WMO standard)
# ═══════════════════════════════════════════════════════════════════════════════
WMO_CODES = {
    0: "Clear sky ☀️",        1: "Mainly clear 🌤️",    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",         45: "Foggy 🌫️",           48: "Icy fog 🌫️",
    51: "Light drizzle 🌦️",  53: "Moderate drizzle 🌦️", 55: "Heavy drizzle 🌧️",
    61: "Slight rain 🌧️",    63: "Moderate rain 🌧️",    65: "Heavy rain 🌧️",
    71: "Slight snow ❄️",     73: "Moderate snow ❄️",    75: "Heavy snow ❄️",
    77: "Snow grains ❄️",     80: "Rain showers 🌦️",    81: "Heavy showers 🌧️",
    95: "Thunderstorm ⛈️",   96: "Thunderstorm+hail ⛈️", 99: "Thunderstorm+hail ⛈️",
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Pakistan city coordinates (fallback when geocoding fails)
# ═══════════════════════════════════════════════════════════════════════════════
PK_CITIES = {
    "lahore":      (31.5497, 74.3436), "karachi":    (24.8608, 67.0104),
    "islamabad":   (33.7294, 73.0931), "rawalpindi": (33.5651, 73.0169),
    "faisalabad":  (31.4180, 73.0790), "multan":     (30.1978, 71.4708),
    "peshawar":    (34.0151, 71.5249), "quetta":     (30.1798, 66.9750),
    "sialkot":     (32.4945, 74.5229), "gujranwala": (32.1877, 74.1945),
    "bahawalpur":  (29.3956, 71.6836), "sargodha":   (32.0740, 72.6861),
    "sahiwal":     (30.6682, 73.1067), "okara":      (30.8138, 73.4534),
    "dera ghazi":  (30.0456, 70.6344), "sukkur":     (27.7052, 68.8574),
    "larkana":     (27.5570, 68.2122), "hyderabad":  (25.3960, 68.3578),
    "abbottabad":  (34.1463, 73.2117), "mardan":     (34.2010, 72.0396),
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Agricultural sowing advice rules
# ═══════════════════════════════════════════════════════════════════════════════

def _assess_sowing_conditions(
    crop: str,
    temp_max: float,
    temp_min: float,
    rain_mm: float,
    wind_kph: float,
    weather_code: int,
) -> Dict:
    """
    Return a sowing suitability assessment for a crop given weather conditions.
    Rules are based on Pakistan Agricultural Research Council (PARC) guidelines.
    """
    crop = crop.lower().strip()
    issues = []
    positives = []
    score = 100  # start at 100, deduct for problems

    # ── Wheat (Rabi — Oct to Nov) ─────────────────────────────────────────────
    if "wheat" in crop:
        if temp_min < 5:
            issues.append(f"Too cold at night ({temp_min}°C) — wheat germination needs >8°C")
            score -= 30
        elif temp_min < 10:
            issues.append(f"Night temperature marginal ({temp_min}°C) — germination may be slow")
            score -= 15
        else:
            positives.append(f"Night temperature good ({temp_min}°C) for wheat germination")

        if temp_max > 30:
            issues.append(f"Daytime too hot ({temp_max}°C) — wheat prefers <28°C during sowing")
            score -= 20
        else:
            positives.append(f"Daytime temperature suitable ({temp_max}°C)")

        if rain_mm > 15:
            issues.append(f"Heavy rain ({rain_mm}mm) — avoid sowing; soil too waterlogged")
            score -= 40
        elif rain_mm > 5:
            issues.append(f"Moderate rain ({rain_mm}mm) — wait 1-2 days for soil to drain")
            score -= 20
        elif rain_mm > 0.5:
            positives.append(f"Light rain ({rain_mm}mm) — good soil moisture for germination")
        else:
            positives.append("Dry conditions — ensure adequate soil moisture before sowing")

    # ── Cotton (Kharif — Apr to May) ─────────────────────────────────────────
    elif "cotton" in crop:
        if temp_min < 18:
            issues.append(f"Too cold ({temp_min}°C min) — cotton needs >20°C night temperature")
            score -= 35
        if temp_max < 25:
            issues.append(f"Daytime temperature low ({temp_max}°C) — cotton needs 25–35°C")
            score -= 25
        if temp_max > 42:
            issues.append(f"Extreme heat ({temp_max}°C) — heat stress above 40°C")
            score -= 30
        if rain_mm > 20:
            issues.append(f"Heavy rain ({rain_mm}mm) — delay sowing 2–3 days")
            score -= 30

    # ── Rice (Kharif — Jun to Jul transplant) ─────────────────────────────────
    elif "rice" in crop:
        if temp_min < 20:
            issues.append(f"Too cool ({temp_min}°C) — rice transplanting needs >22°C")
            score -= 30
        if rain_mm > 30:
            positives.append(f"Heavy rain ({rain_mm}mm) — good for paddy field flooding")
        elif rain_mm < 2 and temp_max > 36:
            issues.append("Dry + hot — ensure standing water in paddy fields")
            score -= 20

    # ── Generic advice for unrecognised crops ─────────────────────────────────
    else:
        if rain_mm > 20:
            issues.append(f"Heavy rain ({rain_mm}mm) — generally avoid field operations")
            score -= 25
        if wind_kph > 30:
            issues.append(f"Strong winds ({wind_kph} kph) — avoid spraying operations")
            score -= 15

    # ── General factors ───────────────────────────────────────────────────────
    if weather_code in [95, 96, 99]:
        issues.append("Thunderstorm expected — avoid field operations entirely")
        score -= 50
    elif weather_code in [65, 75, 81]:
        issues.append("Heavy precipitation forecast — postpone sowing")
        score -= 35

    if wind_kph > 25:
        issues.append(f"High winds ({wind_kph} kph) — avoid spraying or light-seed sowing")
        score -= 10

    score = max(0, min(100, score))

    if score >= 80:
        verdict = "✅ Excellent conditions"
        advice  = "Conditions are ideal. Proceed with sowing."
    elif score >= 60:
        verdict = "🟡 Good conditions with minor concerns"
        advice  = "Conditions are generally suitable. Address the noted concerns."
    elif score >= 40:
        verdict = "⚠️ Marginal — proceed with caution"
        advice  = "Wait if possible, or take precautions to address the listed issues."
    else:
        verdict = "❌ Poor conditions — delay recommended"
        advice  = "Delay sowing until conditions improve. Check the 3-day forecast."

    return {
        "score":     score,
        "verdict":   verdict,
        "advice":    advice,
        "positives": positives,
        "issues":    issues,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Core functions
# ═══════════════════════════════════════════════════════════════════════════════

def _geocode(city: str):
    """Return (lat, lon, canonical_name) for a city using Open-Meteo geocoding."""
    city_key = city.lower().strip()

    # Check our Pakistan city table first (no network needed)
    for k, coords in PK_CITIES.items():
        if k in city_key or city_key in k:
            return coords[0], coords[1], city

    # Fall back to Open-Meteo geocoding API
    try:
        url = (f"https://geocoding-api.open-meteo.com/v1/search"
               f"?name={urllib.parse.quote(city)}&count=1&language=en&format=json")
        with urllib.request.urlopen(url, timeout=6) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        if results:
            res = results[0]
            return res["latitude"], res["longitude"], res.get("name", city)
    except Exception as e:
        print(f"[MCP/weather] Geocoding failed: {e}")

    # Ultimate fallback: Lahore
    print(f"[MCP/weather] Could not geocode '{city}', defaulting to Lahore")
    return 31.5497, 74.3436, "Lahore (default)"


def get_weather_forecast(location: str) -> Dict:
    """
    Fetch current conditions + 7-day forecast for any Pakistan city.
    Returns a structured dict ready for LLM injection.
    """
    lat, lon, city_name = _geocode(location)

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
        f"precipitation,weathercode,apparent_temperature"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        f"weathercode,wind_speed_10m_max,precipitation_probability_max"
        f"&timezone=Asia%2FKarachi&forecast_days=7"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
    except Exception as e:
        return {"error": f"Weather API unavailable: {e}"}

    cur   = data.get("current", {})
    daily = data.get("daily", {})

    current = {
        "temp_c":      cur.get("temperature_2m"),
        "feels_like_c": cur.get("apparent_temperature"),
        "humidity_pct": cur.get("relative_humidity_2m"),
        "wind_kph":    cur.get("wind_speed_10m"),
        "rain_mm":     cur.get("precipitation", 0),
        "condition":   WMO_CODES.get(cur.get("weathercode", 0), "Unknown"),
    }

    forecast = []
    for i, date in enumerate(daily.get("time", [])):
        forecast.append({
            "date":       date,
            "day":        datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
            "max_c":      daily["temperature_2m_max"][i],
            "min_c":      daily["temperature_2m_min"][i],
            "rain_mm":    daily["precipitation_sum"][i],
            "rain_prob":  daily.get("precipitation_probability_max", [None]*7)[i],
            "wind_kph":   daily.get("wind_speed_10m_max", [None]*7)[i],
            "condition":  WMO_CODES.get(daily["weathercode"][i], "Unknown"),
        })

    return {
        "location":    city_name,
        "lat":         lat,
        "lon":         lon,
        "current":     current,
        "forecast_7d": forecast,
        "source":      "Open-Meteo (https://open-meteo.com) — free, no API key",
    }


def get_sowing_advice(location: str, crop: str, target_day: str = "tomorrow") -> Dict:
    """
    Full sowing-advice pipeline:
    1. Fetch weather forecast for location
    2. Pick the target day (today / tomorrow / specific date)
    3. Assess agricultural suitability for the crop
    4. Return structured advice ready for LLM

    Args:
        location:   city/district name, e.g. "Lahore", "Multan"
        crop:       crop name, e.g. "wheat", "cotton", "rice"
        target_day: "today" | "tomorrow" | "YYYY-MM-DD" | day name e.g. "Saturday"

    Returns dict with:
        weather    — raw weather for the target day
        assessment — sowing suitability score + advice
        all_days   — full 7-day forecast (for multi-day comparison)
    """
    weather_data = get_weather_forecast(location)
    if "error" in weather_data:
        return weather_data

    forecast = weather_data["forecast_7d"]
    if not forecast:
        return {"error": "No forecast data returned"}

    # ── Resolve target_day ────────────────────────────────────────────────────
    today_str    = datetime.now().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    target = target_day.lower().strip()
    if target in ("today", "aaj"):
        target_date = today_str
    elif target in ("tomorrow", "kal", "next day"):
        target_date = tomorrow_str
    else:
        # Try matching a weekday name or YYYY-MM-DD
        for day in forecast:
            if target in day["day"].lower() or target == day["date"]:
                target_date = day["date"]
                break
        else:
            target_date = tomorrow_str   # default

    target_forecast = next((d for d in forecast if d["date"] == target_date), forecast[0])

    # ── Assess sowing suitability ─────────────────────────────────────────────
    assessment = _assess_sowing_conditions(
        crop        = crop,
        temp_max    = target_forecast["max_c"],
        temp_min    = target_forecast["min_c"],
        rain_mm     = target_forecast["rain_mm"],
        wind_kph    = target_forecast.get("wind_kph") or 0,
        weather_code= next((d for d in [target_forecast] if True), {}).get("condition", ""),
    )

    # ── Best day in the next 7 days ───────────────────────────────────────────
    best_day = None
    best_score = -1
    for day in forecast:
        s = _assess_sowing_conditions(crop, day["max_c"], day["min_c"], day["rain_mm"], day.get("wind_kph") or 0, "")
        if s["score"] > best_score:
            best_score = s["score"]
            best_day   = {"date": day["date"], "day": day["day"], **s}

    return {
        "location":         weather_data["location"],
        "crop":             crop,
        "target_date":      target_date,
        "target_day_name":  target_forecast["day"],
        "weather":          target_forecast,
        "current":          weather_data["current"],
        "assessment":       assessment,
        "best_day_this_week": best_day,
        "all_7_day_forecast": forecast,
        "source":           "Open-Meteo API (free) · PARC sowing guidelines",
    }


def format_for_llm(advice: Dict) -> str:
    """
    Format sowing advice into a clean context block for the LLM.
    This is injected into the LLM's system prompt before generation.
    """
    if "error" in advice:
        return f"[WEATHER ERROR] {advice['error']}"

    a   = advice.get("assessment", {})
    wx  = advice.get("weather", {})
    cur = advice.get("current", {})
    b   = advice.get("best_day_this_week", {})

    lines = [
        f"WEATHER DATA — {advice['location']} — {advice['target_day_name']} ({advice['target_date']})",
        f"Crop: {advice['crop'].upper()}",
        "",
        f"FORECAST FOR TARGET DAY:",
        f"  Max: {wx.get('max_c')}°C  |  Min: {wx.get('min_c')}°C",
        f"  Rain: {wx.get('rain_mm')}mm  |  Wind: {wx.get('wind_kph')} kph",
        f"  Condition: {wx.get('condition')}  |  Rain probability: {wx.get('rain_prob')}%",
        "",
        f"CURRENT CONDITIONS:",
        f"  Temp: {cur.get('temp_c')}°C (feels like {cur.get('feels_like_c')}°C)",
        f"  Humidity: {cur.get('humidity_pct')}%  |  Wind: {cur.get('wind_kph')} kph",
        f"  Condition: {cur.get('condition')}",
        "",
        f"SOWING ASSESSMENT: {a.get('verdict')} (score: {a.get('score')}/100)",
        f"ADVICE: {a.get('advice')}",
    ]

    if a.get("positives"):
        lines.append("\nFAVOURABLE CONDITIONS:")
        lines.extend(f"  ✓ {p}" for p in a["positives"])

    if a.get("issues"):
        lines.append("\nCONCERNS:")
        lines.extend(f"  ✗ {i}" for i in a["issues"])

    if b:
        lines.append(f"\nBEST DAY THIS WEEK: {b.get('day')} {b.get('date')} (score: {b.get('score')}/100)")

    lines.append(f"\nDATA SOURCE: Open-Meteo API (https://open-meteo.com) | PARC guidelines")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  Terminal test
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("MCP WEATHER ADVISOR — Terminal Test")
    print("=" * 60)

    test_cases = [
        ("Lahore",  "wheat",  "tomorrow"),
        ("Multan",  "cotton", "Saturday"),
        ("Karachi", "rice",   "today"),
    ]

    for location, crop, day in test_cases:
        print(f"\n[TEST] '{day} a good day for {crop} in {location}?'")
        result = get_sowing_advice(location, crop, day)
        print(format_for_llm(result))
        print("-" * 60)

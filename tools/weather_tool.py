"""
tools/weather_tool.py
LangChain tool: Fetch live weather forecast from Open-Meteo API (no key needed).
"""

import requests
from langchain_core.tools import tool
from datetime import datetime, timedelta


# Hardcoded lat/lon for top Indian travel destinations
CITY_COORDS = {
    "goa": (15.2993, 74.1240),
    "manali": (32.2396, 77.1887),
    "shimla": (31.1048, 77.1734),
    "jaipur": (26.9124, 75.7873),
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "agra": (27.1767, 78.0081),
    "varanasi": (25.3176, 82.9739),
    "udaipur": (24.5854, 73.7125),
    "mysore": (12.2958, 76.6394),
    "ooty": (11.4064, 76.6932),
    "munnar": (10.0889, 77.0595),
    "darjeeling": (27.0360, 88.2627),
    "leh": (34.1526, 77.5771),
    "rishikesh": (30.0869, 78.2676),
    "haridwar": (29.9457, 78.1642),
    "amritsar": (31.6340, 74.8723),
    "coorg": (12.3375, 75.8069),
    "andaman": (11.7401, 92.6586),
    "kerala": (10.8505, 76.2711),
    "kochi": (9.9312, 76.2673),
    "surat": (21.1702, 72.8311),
    "ahmedabad": (23.0225, 72.5714),
}

WMO_CODES = {
    0: "Clear Sky ☀️",
    1: "Mainly Clear 🌤️",
    2: "Partly Cloudy ⛅",
    3: "Overcast ☁️",
    45: "Foggy 🌫️",
    48: "Icy Fog 🌫️",
    51: "Light Drizzle 🌦️",
    53: "Drizzle 🌦️",
    55: "Heavy Drizzle 🌧️",
    61: "Slight Rain 🌧️",
    63: "Rain 🌧️",
    65: "Heavy Rain 🌧️",
    71: "Slight Snow 🌨️",
    73: "Snow 🌨️",
    75: "Heavy Snow ❄️",
    80: "Rain Showers 🌦️",
    81: "Rain Showers 🌦️",
    82: "Violent Rain Showers ⛈️",
    95: "Thunderstorm ⛈️",
    96: "Thunderstorm + Hail ⛈️",
    99: "Thunderstorm + Heavy Hail ⛈️",
}


def get_coords(city: str) -> tuple[float, float] | None:
    """Get lat/lon for a city. Returns None if not found."""
    return CITY_COORDS.get(city.strip().lower())


def fetch_weather_raw(city: str, start_date: str, num_days: int = 3) -> dict:
    """
    Fetch weather forecast from Open-Meteo.
    start_date: 'YYYY-MM-DD'
    Returns dict with day-wise forecast list.
    """
    coords = get_coords(city)
    if not coords:
        return {"error": f"City '{city}' not in database. Add coordinates to CITY_COORDS dict."}

    lat, lon = coords

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        start = datetime.now()

    end = start + timedelta(days=num_days - 1)
    end_date = end.strftime("%Y-%m-%d")
    start_date_str = start.strftime("%Y-%m-%d")

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,windspeed_10m_max"
        f"&timezone=Asia%2FKolkata"
        f"&start_date={start_date_str}&end_date={end_date}"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return {"error": f"Weather API failed: {str(e)}"}

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    codes = daily.get("weathercode", [])
    precip = daily.get("precipitation_sum", [])
    wind = daily.get("windspeed_10m_max", [])

    forecast = []
    for i, date in enumerate(dates):
        code = codes[i] if i < len(codes) else 0
        forecast.append({
            "date": date,
            "max_temp": max_temps[i] if i < len(max_temps) else "N/A",
            "min_temp": min_temps[i] if i < len(min_temps) else "N/A",
            "condition": WMO_CODES.get(code, f"Code {code}"),
            "precipitation_mm": precip[i] if i < len(precip) else 0,
            "wind_kmh": wind[i] if i < len(wind) else 0,
        })

    return {"city": city, "forecast": forecast, "lat": lat, "lon": lon}


@tool
def weather_lookup_tool(query: str) -> str:
    """
    Get weather forecast for a city during travel dates.
    Input format: 'city:Goa date:2024-12-15 days:3'
    OR plain text like 'weather in Goa from December 15 for 3 days'
    Returns day-wise temperature, conditions, rain, and wind forecast.
    """
    try:
        params = {}
        for part in query.split():
            if ":" in part:
                k, v = part.split(":", 1)
                params[k.lower()] = v

        city = params.get("city", "")
        start_date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        num_days = int(params.get("days", 3))

        # Natural language fallback
        if not city:
            words = query.lower().split()
            for kw in ["in", "for", "at"]:
                if kw in words:
                    idx = words.index(kw)
                    city = words[idx + 1].title() if idx + 1 < len(words) else ""
                    break

        if not city:
            return "Error: Please provide a city name."

        result = fetch_weather_raw(city, start_date, num_days)

        if result.get("error"):
            return result["error"]

        forecast = result["forecast"]
        output = [f"🌤  WEATHER FORECAST — {city.upper()}", ""]

        for day in forecast:
            rain_warn = " ☔ Carry umbrella!" if day["precipitation_mm"] > 5 else ""
            output.append(
                f"  📅 {day['date']}: {day['condition']}"
                f" | 🌡 {day['min_temp']}°C – {day['max_temp']}°C"
                f" | 💨 Wind {day['wind_kmh']} km/h"
                f" | 🌧 Rain {day['precipitation_mm']} mm{rain_warn}"
            )

        return "\n".join(output)

    except Exception as e:
        return f"Weather lookup error: {str(e)}"
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
import os

import httpx


OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


async def geocode_location(name: str) -> Optional[Tuple[float, float]]:
    """
    Resolve a freeform place name to (latitude, longitude) using Open-Meteo geocoding.
    Returns None if not found.
    """
    if not name:
        return None
    params = {"name": name, "count": 1}
    timeout = httpx.Timeout(6.0, connect=3.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(OPEN_METEO_GEOCODE_URL, params=params)
            resp.raise_for_status()
            data = resp.json() or {}
            results = data.get("results") or []
            if not results:
                print(f"[WEATHER] Geocode returned no results for '{name}'")
                return None
            first = results[0]
            return float(first["latitude"]), float(first["longitude"])
        except Exception as e:
            print(f"[WEATHER] Geocode error for '{name}': {e}")
            return None


async def get_weather_summary(place_name: str, event_time: datetime) -> Optional[Dict[str, Any]]:
    """
    Fetch a lightweight weather summary for a place name at a given datetime.
    Uses Open-Meteo hourly forecast and picks the hour closest to event_time.
    Returns a dict with keys: temperature_c, precipitation_probability, wind_speed_kmh, conditions (string).
    """
    if event_time.tzinfo is None:
        # Treat naive DB timestamps as local time for better alignment with 'timezone=auto'
        event_time = event_time.replace(tzinfo=None)

    # Try to geocode provided place name
    coords = await geocode_location(place_name)
    # Fallback to DEFAULT_WEATHER_CITY if provided and initial geocode fails
    if not coords:
        default_city = os.getenv("DEFAULT_WEATHER_CITY")
        if default_city and default_city.lower() != (place_name or "").lower():
            print(f"[WEATHER] Falling back to DEFAULT_WEATHER_CITY='{default_city}'")
            coords = await geocode_location(default_city)
    if not coords:
        return None

    lat, lon = coords
    date_str = (event_time.date().isoformat())
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation_probability,weather_code,wind_speed_10m",
        "start_date": date_str,
        "end_date": date_str,
        "timezone": "auto",
    }
    timeout = httpx.Timeout(6.0, connect=3.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(OPEN_METEO_FORECAST_URL, params=params)
            resp.raise_for_status()
            data = resp.json() or {}
            hourly = (data.get("hourly") or {})
            times = hourly.get("time") or []
            temps = hourly.get("temperature_2m") or []
            precip = hourly.get("precipitation_probability") or []
            wind = hourly.get("wind_speed_10m") or []
            wcode = hourly.get("weather_code") or []
            if not times:
                print(f"[WEATHER] No hourly times returned for {place_name} on {date_str}")
                return None

            # Find closest hour index
            # Normalize both event_time and API times to naive local for comparison
            target_dt = event_time.replace(minute=0, second=0, microsecond=0, tzinfo=None)
            def parse_dt(s: str) -> datetime:
                try:
                    return datetime.fromisoformat(s)
                except Exception:
                    return target_dt
            deltas = [abs((parse_dt(t) - target_dt).total_seconds()) for t in times]
            idx = deltas.index(min(deltas))

            def safe_get(arr, i, default=None):
                try:
                    return arr[i]
                except Exception:
                    return default

            temp_c = safe_get(temps, idx)
            precip_prob = safe_get(precip, idx)
            wind_speed = safe_get(wind, idx)
            code = safe_get(wcode, idx)

            condition = _describe_weather_code(code)

            return {
                "temperature_c": temp_c,
                "precipitation_probability": precip_prob,
                "wind_speed_kmh": wind_speed,
                "conditions": condition,
                "latitude": lat,
                "longitude": lon,
            }
        except Exception as e:
            print(f"[WEATHER] Forecast error for '{place_name}' ({lat},{lon}) on {date_str}: {e}")
            return None


def _describe_weather_code(code: Optional[int]) -> str:
    # Basic mapping for common codes; Open-Meteo WMO weather interpretation codes
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Drizzle",
        55: "Dense drizzle",
        56: "Freezing drizzle",
        57: "Freezing drizzle",
        61: "Slight rain",
        63: "Rain",
        65: "Heavy rain",
        66: "Freezing rain",
        67: "Freezing rain",
        71: "Slight snow",
        73: "Snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Rain showers",
        82: "Violent rain showers",
        85: "Snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }
    return mapping.get(int(code) if code is not None else -1, "Unknown conditions")



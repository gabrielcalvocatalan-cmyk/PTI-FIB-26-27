from typing import Any

import csv
import logging
import os
import sys

logging.basicConfig(
    level=logging.ERROR,   # only ERROR level=logging.INFO,  # show INFO and above
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],  # stderr is often safest with stdio
    force=True,  # IMPORTANT: override any existing logging config
)

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("pti")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""

RENTALS_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "chatbot-car_rental", "dataset", "rentals.csv",
)

@mcp.tool()
async def list_rentals() -> str:
    """Fetch the current car rental list from the local dataset."""
    print(">>> list_rentals CALLED", file=sys.stderr, flush=True)

    logging.info("Reading rentals from %s", RENTALS_CSV)

    try:
        with open(RENTALS_CSV, newline="") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        logging.exception("rentals.csv not found")
        return "Error: rentals.csv not found at %s" % RENTALS_CSV

    body_preview = str(rows[:3])
    logging.info("Rentals read (first 3 rows): %s", body_preview)

    lines = [", ".join(f"{k}={v}" for k, v in row.items()) for row in rows]
    return "\n".join(lines)


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location. This is a US-only API (api.weather.gov);
    other locations will return a 404.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location. US locations are west of Greenwich,
            so this must be negative (e.g. -74.0 for New York, not 74.0).
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period["name"]}:
Temperature: {period["temperature"]}°{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period["detailedForecast"]}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

import httpx

@mcp.tool()
async def get_recent_earthquakes(min_magnitude: float = 4.5) -> str:
    """Obtiene una lista de terremotos recientes en el mundo que superan 
    una magnitud mínima especificada utilizando la API pública del USGS.

    Args:
        min_magnitude: Magnitud mínima (por ejemplo, 4.5 o 5.0).
    """
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude={min_magnitude}&limit=5"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        
    if response.status_code != 200:
        return "No se ha podido conectar con el servicio de terremotos."
        
    data = response.json()
    features = data.get("features", [])
    
    if not features:
        return "No se han encontrado terremotos recientes con esa magnitud."

    earthquakes = []
    for quake in features:
        props = quake["properties"]
        place = props.get("place", "Ubicación desconocida")
        mag = props.get("mag")
        
        report = f"""
Ubicación: {place}
Magnitud: {mag} Richter
"""
        earthquakes.append(report.strip())

    return "\n---\n".join(earthquakes)
    
def main():
    # Initialize and run the server
    logging.info("Initialize and run the server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

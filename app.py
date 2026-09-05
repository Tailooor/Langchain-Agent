# Weather Agent — LangChain agent that finds a location and returns its country + detailed weather.
#
# Usage:
#   CLI:    python app.py
#   Import: from app import run_agent
#
# Required env vars (loaded from .env):
#   WEATHER_API_KEY    - WeatherAPI.com key
#   OPENROUTER_API_KEY - OpenRouter key (model provider)
#   TAVILY_API_KEY     - Tavily search key
#   LANGSMITH_API_KEY  - LangSmith key (used to pull the ReAct prompt)

import os
import certifi
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langsmith import Client
from langchain.agents import create_agent
from langchain.tools import tool
import requests

# Load secrets from .env and point SSL at the certifi bundle (fixes some HTTPS issues on Windows).
load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
os.environ["SSL_CERT_FILE"] = certifi.where()

# Web search tool — the agent uses this to identify/confirm the user-supplied location.
search_tool = TavilySearch(max_results=2)

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a given location.

    Hits WeatherAPI's /current.json endpoint and returns a human-readable
    report including country, local time, temperature, feels-like, humidity,
    wind, pressure, precipitation, cloud cover, and UV index.
    """
    # Build the request to WeatherAPI's current-conditions endpoint.
    url = "https://api.weatherapi.com/v1/current.json"
    params = {"key": WEATHER_API_KEY, "q": location, "aqi": "no"}

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f"Error fetching weather for {location}: HTTP {response.status_code}"

    # Parse the response into location + current-condition sections.
    data = response.json()
    loc = data.get("location", {})
    cur = data.get("current", {})
    cond = cur.get("condition", {})

    # Extract identifying fields (name, region, country, localtime).
    name = loc.get("name", location)
    region = loc.get("region", "")
    country = loc.get("country", "Unknown")
    localtime = loc.get("localtime", "")

    # Extract current-condition fields.
    temp_c = cur.get("temp_c")
    temp_f = cur.get("temp_f")
    feelslike_c = cur.get("feelslike_c")
    humidity = cur.get("humidity")
    wind_kph = cur.get("wind_kph")
    wind_dir = cur.get("wind_dir")
    pressure_mb = cur.get("pressure_mb")
    precip_mm = cur.get("precip_mm")
    cloud = cur.get("cloud")
    uv = cur.get("uv")
    condition_text = cond.get("text", "N/A")

    # Build a clean "<name>[, <region>], <country>" string (avoid duplicating name==region).
    location_str = name
    if region and region.lower() != name.lower():
        location_str += f", {region}"
    location_str += f", {country}"

    # Compose the final readable report the agent will relay back to the user.
    return (
        f"Weather for {location_str} (local time: {localtime}):\n"
        f"- Condition: {condition_text}\n"
        f"- Temperature: {temp_c}°C ({temp_f}°F), feels like {feelslike_c}°C\n"
        f"- Humidity: {humidity}%\n"
        f"- Wind: {wind_kph} kph {wind_dir}\n"
        f"- Pressure: {pressure_mb} mb\n"
        f"- Precipitation: {precip_mm} mm\n"
        f"- Cloud cover: {cloud}%\n"
        f"- UV index: {uv}"
    )

# LangSmith client — used to fetch the ReAct prompt template at runtime.
client = Client()

# Pull the prompt deployment or artifact directly from the Hub.
# This is the standard "hwchase17/react" ReAct prompt: it tells the model to
# reason step-by-step, pick a tool, observe the result, and repeat until done.
prompt = client.pull_prompt("hwchase17/react", dangerously_pull_public_prompt=True)

# Build the agent: an OpenRouter-hosted LLM + search + weather tools,
# guided by the ReAct system prompt.
agent = create_agent(
    model="openrouter:minimax/minimax-m3:free",
    tools=[search_tool, get_weather],
    system_prompt=prompt.template
)


def run_agent(query: str) -> str:
    """Invoke the agent with a single user query and return the final assistant message.

    Used by both the CLI entrypoint below and the Flask web GUI (web_gui.py).
    """
    # Run the agent with a single human turn and grab the final message.
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    messages = result.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    content = getattr(last, "content", last)
    # Handle both string content and list-of-parts content (e.g. multimodal responses).
    if isinstance(content, list):
        return "\n".join(
            part.get("text", str(part)) if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content)


if __name__ == "__main__":
    # CLI demo: print the weather for San Francisco when launched directly.
    print(run_agent("What is the current weather in San Francisco?"))
import os
import certifi
# from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langsmith import Client
from langchain.agents import create_agent
from langchain.tools import tool
import requests

load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
os.environ["SSL_CERT_FILE"] = certifi.where()

search_tool = TavilySearch(max_results=2)

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a given location."""
    url = "https://api.weatherapi.com/v1/current.json"
    params = {"key": WEATHER_API_KEY, "q": location, "aqi": "no"}

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f"Error fetching weather for {location}: HTTP {response.status_code}"

    data = response.json()
    loc = data.get("location", {})
    cur = data.get("current", {})
    cond = cur.get("condition", {})

    name = loc.get("name", location)
    region = loc.get("region", "")
    country = loc.get("country", "Unknown")
    localtime = loc.get("localtime", "")

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

    location_str = name
    if region and region.lower() != name.lower():
        location_str += f", {region}"
    location_str += f", {country}"

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

client = Client()

# Pull the prompt deployment or artifact directly from the Hub
prompt = client.pull_prompt("hwchase17/react", dangerously_pull_public_prompt=True)

agent = create_agent(
    model="openrouter:minimax/minimax-m3:free",
    tools=[search_tool, get_weather],
    system_prompt=prompt.template
)


def run_agent(query: str) -> str:
    """Invoke the agent with a single user query and return the final assistant message."""
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    messages = result.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    content = getattr(last, "content", last)
    if isinstance(content, list):
        return "\n".join(
            part.get("text", str(part)) if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content)


if __name__ == "__main__":
    print(run_agent("What is the current weather in San Francisco?"))
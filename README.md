# Weather Agent

A LangChain agent that searches for a location and returns its **current weather**, **country**, and **detailed conditions**. Includes a simple Flask web GUI.

## Features

- Search any location and get its country.
- Detailed current weather: temperature, feels-like, humidity, wind, pressure, precipitation, cloud cover, UV index.
- Two ways to use it:
  - **CLI**: run `app.py` directly.
  - **Web GUI**: launch `web_gui.py` and open it in your browser.

## Project Structure

```
.
├── app.py            # Weather agent + get_weather tool
├── web_gui.py        # Flask web GUI (frontend + /api/weather endpoint)
├── requirements.txt
├── .env              # API keys (not committed, see .gitignore)
└── .gitignore
```

## Requirements

- Python 3.10+
- A [WeatherAPI](https://www.weatherapi.com/) key
- An [OpenRouter](https://openrouter.ai/) API key
- A [Tavily](https://tavily.com/) API key (for web search)
- A [LangSmith](https://smith.langchain.com/) API key (used to pull the prompt template)

## Installation

```bash
# Create and activate a conda env (or use venv)
conda create -n langagent python=3.11
conda activate langagent

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with the following keys:

```env
WEATHER_API_KEY=your_weatherapi_key
OPENROUTER_API_KEY=your_openrouter_key
TAVILY_API_KEY=your_tavily_key
LANGSMITH_API_KEY=your_langsmith_key
```

## Usage

### Option 1: Web GUI (recommended)

```bash
python web_gui.py
```

Then open <http://127.0.0.1:5000> in your browser. Type a location (e.g. `Cairo`, `Tokyo, Japan`) and click **Search**. The agent will identify the place, look up the weather, and display the country and detailed conditions.

To change the port:

```bash
PORT=8080 python web_gui.py
```

### Option 2: CLI

```bash
python app.py
```

By default it prints the weather for **San Francisco**. Edit the `if __name__ == "__main__"` block at the bottom of `app.py` to ask anything else, or import `run_agent` from another script:

```python
from app import run_agent

print(run_agent("Find the location 'Reykjav'k' and give me its current weather, country, and detailed conditions."))
```

## How It Works

1. The user submits a location through the GUI or CLI.
2. The agent (built with `create_agent` from `langchain.agents`) receives the query.
3. It uses **TavilySearch** to identify the location (name, region, country).
4. It calls the **`get_weather`** tool, which hits the WeatherAPI `/current.json` endpoint and returns a structured report including:
   - Country and region
   - Local time
   - Temperature (°C / °F) and feels-like
   - Humidity, wind (speed + direction), pressure
   - Precipitation, cloud cover, UV index
5. The final response is rendered in the GUI or printed to the terminal.

The agent uses the `hwchase17/react` prompt template pulled from LangSmith.

## Notes

- Never commit your `.env` file — it is excluded by `.gitignore`.
- The model in use is `minimax/minimax-m3:free` via OpenRouter. You can change it in `app.py` if you want a different model.
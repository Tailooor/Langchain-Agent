"""Simple Flask web GUI for the weather agent.

Run:
    python web_gui.py

Then open http://127.0.0.1:5000 in a browser.
"""
import os
import sys

from flask import Flask, jsonify, render_template_string, request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import run_agent

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Weather Agent</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --accent: #38bdf8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .card {
      background: var(--card);
      border-radius: 16px;
      padding: 32px;
      width: 100%;
      max-width: 640px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    }
    h1 { margin: 0 0 8px; font-size: 28px; }
    p.sub { margin: 0 0 24px; color: var(--muted); }
    form { display: flex; gap: 8px; }
    input[type=text] {
      flex: 1;
      padding: 12px 14px;
      border-radius: 10px;
      border: 1px solid #334155;
      background: #0f172a;
      color: var(--text);
      font-size: 16px;
      outline: none;
    }
    input[type=text]:focus { border-color: var(--accent); }
    button {
      padding: 12px 20px;
      border-radius: 10px;
      border: none;
      background: var(--accent);
      color: #0f172a;
      font-weight: 600;
      cursor: pointer;
      font-size: 16px;
    }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    .result {
      margin-top: 24px;
      padding: 18px;
      background: #0f172a;
      border-radius: 10px;
      white-space: pre-wrap;
      line-height: 1.6;
      min-height: 80px;
      border: 1px solid #334155;
    }
    .error { color: #fca5a5; }
    .placeholder { color: var(--muted); font-style: italic; }
    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid #94a3b8;
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      vertical-align: middle;
      margin-right: 6px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .examples { margin-top: 14px; font-size: 13px; color: var(--muted); }
    .examples span { cursor: pointer; color: var(--accent); margin-right: 8px; }
    .examples span:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Weather Agent</h1>
    <p class="sub">Ask for a location and get the current weather, country, and details.</p>
    <form id="form">
      <input id="q" name="q" type="text" placeholder="e.g. Cairo, Egypt" autocomplete="off" required>
      <button id="btn" type="submit">Search</button>
    </form>
    <div class="examples">
      Try:
      <span onclick="document.getElementById('q').value='Cairo'">Cairo</span>
      <span onclick="document.getElementById('q').value='Tokyo, Japan'">Tokyo</span>
      <span onclick="document.getElementById('q').value='San Francisco'">San Francisco</span>
    </div>
    <div class="result placeholder" id="out">Results will appear here.</div>
  </div>

<script>
const form = document.getElementById('form');
const input = document.getElementById('q');
const btn = document.getElementById('btn');
const out = document.getElementById('out');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;
  btn.disabled = true;
  out.classList.remove('placeholder', 'error');
  out.innerHTML = '<span class="spinner"></span>Searching weather for "' + q + '"...';

  try {
    const res = await fetch('/api/weather', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q })
    });
    const data = await res.json();
    if (data.error) {
      out.classList.add('error');
      out.textContent = 'Error: ' + data.error;
    } else {
      out.textContent = data.answer;
    }
  } catch (err) {
    out.classList.add('error');
    out.textContent = 'Network error: ' + err.message;
  } finally {
    btn.disabled = false;
  }
});
</script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_HTML)


@app.route("/api/weather", methods=["POST"])
def api_weather():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Query is required."}), 400

    user_request = (
        f"Find the location '{query}' and give me its current weather, "
        "country, and detailed conditions."
    )
    try:
        answer = run_agent(user_request)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({"query": query, "answer": answer})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
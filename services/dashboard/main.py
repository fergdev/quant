from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import redis.asyncio as redis
import asyncio
import json
from collections import deque, defaultdict
from jinja2 import Template
import numpy as np

app = FastAPI()

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

PRICE_CHANNEL = "price_updates"
SIGNAL_CHANNEL = "trade_signals"
PNL_CHANNEL = "executor_pnl"
TRADE_HISTORY_KEY = "trade_history"

price_log = deque(maxlen=10)
signal_log = deque(maxlen=10)
latest_pnl = {}
trade_history = []
sharpe_ratio = 0.0
symbol_prices = defaultdict(lambda: deque(maxlen=50))

html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>Quant Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { text-align: center; }
        nav { display: flex; justify-content: center; gap: 20px; margin-bottom: 30px; }
        .tab { padding: 10px 20px; background: #eee; border-radius: 5px; cursor: pointer; }
        .tab:hover { background: #ddd; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 4px; }
        .chart-container { margin: 20px 0; }
    </style>
    <script>
        function showTab(id) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            localStorage.setItem('activeTab', id);
        }

        function showChart(symbol) {
            document.querySelectorAll('.chart-container').forEach(el => el.style.display = 'none');
            const container = document.getElementById(`chart-container-${symbol}`);
            if (container) container.style.display = 'block';
            localStorage.setItem('activeSymbol', symbol);
        }

        function fetchDashboardData() {
            fetch("/")
                .then(res => res.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    document.body.innerHTML = doc.body.innerHTML;
                    const tab = localStorage.getItem('activeTab') || 'prices';
                    showTab(tab);
                });
        }

        window.onload = () => {
            const tab = localStorage.getItem('activeTab') || 'prices';
            showTab(tab);
            const activeSymbol = localStorage.getItem('activeSymbol') || document.querySelectorAll('.chart-container')[0]?.id.replace('chart-container-', '');
            if (activeSymbol) showChart(activeSymbol);
            setTimeout(renderCharts, 100);
            setInterval(fetchDashboardData, 5000);
        };

        window.renderCharts = function () {
            {% for symbol, prices in charts.items() %}
            const ctx{{ loop.index }} = document.getElementById("chart-{{ symbol }}");
            if (ctx{{ loop.index }}) {
                new Chart(ctx{{ loop.index }}, {
                    type: 'line',
                    data: {
                        labels: [...Array({{ prices|length }}).keys()],
                        datasets: [{
                            label: '{{ symbol }} Price',
                            data: {{ prices }},
                            borderColor: 'blue',
                            fill: false
                        }]
                    },
                    options: { scales: { x: { display: false } } }
                });
            }
            {% endfor %}
        };
    </script>
</head>
<body>
    <h1>📊 Quant Dashboard</h1>
    <nav>
        <div class="tab" onclick="showTab('prices')">Market Data</div>
        <div class="tab" onclick="showTab('signals')">Trade Signals</div>
        <div class="tab" onclick="showTab('executor')">Executor Status</div>
    </nav>

    <div id="prices" class="tab-content">
        <h2>Latest Market Data</h2>
        <div style="display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-bottom: 20px;">
            {% for symbol in charts.keys() %}
                <button class="tab" onclick="showChart('{{ symbol }}')">{{ symbol }}</button>
            {% endfor %}
        </div>
        {% for symbol, prices in charts.items() %}
        <div id="chart-container-{{ symbol }}" class="chart-container" style="display: none;">
            <h3>{{ symbol }}</h3>
            <canvas id="chart-{{ symbol }}"></canvas>
        </div>
        {% endfor %}
    </div>

    <div id="signals" class="tab-content">
        <h2>Latest Trade Signals</h2>
        {% for item in signals %}
            <pre>{{ item }}</pre>
        {% endfor %}
    </div>

    <div id="executor" class="tab-content">
        <h2>Executor Status</h2>
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr><th>Cash</th><td>${{ "%.2f"|format(pnl.get('cash', 0.0)) }}</td></tr>
            <tr><th>Position</th><td>{{ pnl.get('position', 0) }}</td></tr>
            <tr><th>Entry Price</th><td>${{ "%.2f"|format(pnl.get('entry_price')) if pnl.get('entry_price') is not none else "—" }}</td></tr>
            <tr><th>PnL</th><td>${{ "%.2f"|format(pnl.get('pnl', 0.0)) }}</td></tr>
            <tr><th>Drawdown</th><td>${{ "%.2f"|format(pnl.get('drawdown', 0.0)) }}</td></tr>
            <tr><th>Sharpe Ratio</th><td>{{ "%.2f"|format(sharpe) }}</td></tr>
        </table>
        {% if history %}
        <h3>Trade History (latest 10)</h3>
        {% for entry in history %}
            <pre>{{ entry }}</pre>
        {% endfor %}
        {% endif %}
    </div>
</body>
</html>
""")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    global trade_history, sharpe_ratio
    return html_template.render(prices=list(price_log), signals=list(signal_log), pnl=latest_pnl, history=trade_history, sharpe=sharpe_ratio, charts={symbol: list(prices) for symbol, prices in symbol_prices.items()})

async def subscribe_channels():
    global trade_history, sharpe_ratio
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(PRICE_CHANNEL, SIGNAL_CHANNEL, PNL_CHANNEL)
    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"].replace("'", '"'))
                if message["channel"] == PRICE_CHANNEL:
                    price_log.appendleft(data)
                    symbol = data.get("s")
                    close = data.get("c")
                    if symbol and close is not None:
                        symbol_prices[symbol].append(close)
                elif message["channel"] == SIGNAL_CHANNEL:
                    signal_log.appendleft(data)
                elif message["channel"] == PNL_CHANNEL:
                    global latest_pnl
                    latest_pnl = data
                    raw = await redis_client.lrange(TRADE_HISTORY_KEY, -10, -1)
                    trade_history = [json.loads(item) for item in raw]

                    # Calculate Sharpe ratio from Redis-stored returns
                    returns_raw = await redis_client.lrange("returns", 0, -1)
                    returns = [float(r) for r in returns_raw if r not in (None, "")]
                    if len(returns) >= 2:
                        mean_return = np.mean(returns)
                        std_return = np.std(returns)
                        sharpe_ratio = (mean_return / std_return) if std_return > 0 else 0
                    else:
                        sharpe_ratio = 0
            except Exception as e:
                print("❌ Error processing pubsub message:", e)

@app.on_event("startup")
async def startup():
    asyncio.create_task(subscribe_channels())

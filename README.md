# Quant Trading Platform 🚀

This is a modular, distributed quantitative trading system designed for scalability, real-time decision-making, and deep observability.

---

## 🧠 Overview

This project consists of several microservices built using FastAPI and Python, each with a dedicated role in a quantitative trading system:

- `market-data`: Polls real or mock data and pushes it into Redis
- `strategy-*`: Runs trading strategies like SMA, Momentum, Mean Reversion
- `signal-aggregator`: Aggregates strategy signals into a unified trade signal
- `trade-executor`: Executes trades, tracks position, cash, PnL, and drawdown
- `dashboard`: Visual UI for monitoring market data, signals, executor status
- `observer`: Internal system inspector for debugging and visibility

---

## 📦 Services

| Service            | Description                                        |
|--------------------|----------------------------------------------------|
| `market-data`      | Publishes price bars from Alpaca or mock feed     |
| `strategy-sma`     | Simple Moving Average crossover strategy          |
| `strategy-momentum`| Momentum-based buy/sell signal                    |
| `strategy-meanrev` | Mean reversion signal when price deviates from avg|
| `signal-aggregator`| Consolidates multiple strategies into final signal|
| `trade-executor`   | Executes trades, tracks state, publishes PnL      |
| `dashboard`        | Frontend with charts and executor summary         |
| `observer`         | Internal console to view full system activity     |

---

## 🛠 Tech Stack

- **Python** / **FastAPI** for services
- **Redis** pub/sub for streaming data
- **Docker Compose** to orchestrate everything
- **Prometheus** / **Grafana** / **Loki** / **RedisInsight** for observability
- **Chart.js** for frontend price charts

---

## 🧪 How to Run

```bash
# Start all services
docker-compose up --build

# (or with full observability stack)
docker-compose -f docker-compose.observability.yml up -d
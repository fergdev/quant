# 🧠 Strategy Engine

A FastAPI microservice that runs a basic trading strategy (e.g. simple moving average crossover) based on historical price data.

---

## 🚀 Getting Started

### 1. Create and activate a virtual environment
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🧪 Running Locally
```bash
uvicorn main:app --reload --port 8002
```

Then test:
```bash
curl "http://localhost:8002/?symbol=AAPL&short=5&long=20"
```

---

## 📦 Docker (Optional)
```bash
docker build -t strategy-engine .
docker run --rm -p 8002:80 strategy-engine
```

---

## 🔁 Endpoint

### GET /
Runs the strategy using historical data (assumes external price source or internal stub).

**Params:**
- `symbol` (str): e.g. `AAPL`
- `short` (int): short window for SMA
- `long` (int): long window for SMA

Returns:
- A JSON array of strategy signals and indicators

---

## 🔮 TODOs
- Fetch real price data from `market-data-service`
- Add support for multiple strategies
- Return PnL / trade decisions
- Store outputs in database
- Add test suite
import asyncio
import redis.asyncio as redis
import pandas as pd
from fastapi import FastAPI
import json
from collections import defaultdict

app = FastAPI()

STRATEGY_NAME = "meanrev"
REDIS_PRICE_CHANNEL = "price_updates"
REDIS_SIGNAL_CHANNEL = "trade_signals"
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

price_window = defaultdict(list)
MAX_WINDOW = 20

@app.get("/")
def root():
    return {"message": f"Strategy Engine ({STRATEGY_NAME}) is live"}

async def consume_price_stream():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(REDIS_PRICE_CHANNEL)

    async for message in pubsub.listen():
        if message['type'] != 'message':
            continue

        try:
            bar = json.loads(message['data'].replace("'", '"'))
            symbol = bar['s']
            price = bar['c']
            price_window[symbol].append(price)

            if len(price_window[symbol]) > MAX_WINDOW:
                price_window[symbol].pop(0)

            if len(price_window[symbol]) >= MAX_WINDOW:
                mean = sum(price_window[symbol]) / len(price_window[symbol])

                if price < mean * 0.98:
                    signal = "BUY"
                elif price > mean * 1.02:
                    signal = "SELL"
                else:
                    signal = "HOLD"

                output = {
                    "strategy": STRATEGY_NAME,
                    "symbol": symbol,
                    "signal": signal,
                    "confidence": 1.0
                }
                await redis_client.publish(REDIS_SIGNAL_CHANNEL, json.dumps(output))
                print(f"📤 {symbol}: {signal} (price={price:.2f}, mean={mean:.2f})")

        except Exception as e:
            print("Error processing message:", e)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_price_stream())

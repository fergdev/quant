import asyncio
import redis.asyncio as redis
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

TRADE_SIGNAL_CHANNEL = "trade_signals"
PRICE_CHANNEL = "price_updates"
EXECUTOR_PNL_CHANNEL = "executor_pnl"

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

state = {
    "cash": 100000.0,
    "position": 0,
    "entry_price": None,
    "pnl": 0.0,
    "drawdown": 0.0,
    "history": []
}

latest_price = None

async def handle_signals():
    try:
        await redis_client.ping()
        logging.info("Connected to Redis.")
    except Exception as e:
        logging.error("❌ Redis not available: %s", e)
        return

    pubsub = redis_client.pubsub()
    await pubsub.subscribe("aggregated_signals", PRICE_CHANNEL)
    logging.info("✅ Executor subscribed to channels: 'aggregated_signals', '%s'", PRICE_CHANNEL)

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue

        try:
            channel = message["channel"]
            data = json.loads(message["data"])

            if channel == PRICE_CHANNEL:
                global latest_price
                latest_price = data.get("c")  # close price
                logging.debug(f"💰 Updated latest price: {latest_price}")
                continue

            if channel == "aggregated_signals":
                if latest_price is None:
                    logging.warning("No price available yet, skipping signal.")
                    continue

                symbol = data.get("symbol")
                signal = data.get("signal")
                now = datetime.utcnow().isoformat()
                price = latest_price

                logging.info("Received signal: %s for %s", signal, symbol)

                if signal == "BUY" and state["cash"] >= price:
                    state["position"] += 1
                    state["cash"] -= price
                    state["entry_price"] = price
                    logging.info("BUY executed @ %s. New position: %s, Cash: %s", price, state["position"], state["cash"])
                    state["history"].append({"symbol": symbol, "signal": signal, "time": now, "price": price})

                elif signal == "SELL" and state["position"] > 0 and state["entry_price"] is not None:
                    state["position"] -= 1
                    state["cash"] += price
                    pnl = price - state["entry_price"]
                    state["pnl"] += pnl
                    state["entry_price"] = None
                    logging.info("SELL executed @ %s. PnL realized: %s, New cash: %s", price, pnl, state["cash"])
                    state["history"].append({"symbol": symbol, "signal": signal, "time": now, "price": price})

                else:
                    logging.warning("Signal ignored (insufficient cash/position): %s", signal)

                state["drawdown"] = min(state["drawdown"], state["pnl"] if state["pnl"] < 0 else 0)

                await redis_client.publish(EXECUTOR_PNL_CHANNEL, json.dumps(state))
                await redis_client.rpush("trade_history", json.dumps({
                    "symbol": symbol,
                    "signal": signal,
                    "time": now,
                    "price": price
                }))
                await redis_client.ltrim("trade_history", -100, -1)

                logging.debug("Published executor state: %s", state)

        except Exception as e:
            logging.exception("❌ Executor error: %s", e)

if __name__ == "__main__":
    asyncio.run(handle_signals())

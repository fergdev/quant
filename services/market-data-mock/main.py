import asyncio
import redis.asyncio as redis
import json
from datetime import datetime
import random

REDIS_CHANNEL = "price_updates"
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)
SYMBOLS = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]

async def publish_mock_data():
    while True:
        for symbol in SYMBOLS:
            price = random.uniform(100, 500)  # or add realistic variations
            bar = {
                "s": symbol,
                "t": datetime.utcnow().isoformat(),
                "o": price,
                "h": price * 1.01,
                "l": price * 0.99,
                "c": price,
                "v": random.randint(100, 1000)
            }
            await redis_client.publish(REDIS_CHANNEL, json.dumps(bar))
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(publish_mock_data())
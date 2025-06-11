import asyncio
import json
import websockets
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv(), override=True)
API_KEY = os.getenv("CCDATA_API_KEY")


async def coindesk():
    # this is where you paste your api key
    api_key = API_KEY
    url = "wss://streamer.cryptocompare.com/v2?api_key=" + api_key
    async with websockets.connect(url) as websocket:
        await websocket.send(
            json.dumps(
                {
                    "action": "SubAdd",
                    "subs": ["24~CCCAGG~BTC~USD~m"],
                }
            )
        )
        while True:
            try:
                data = await websocket.recv()
            except websockets.ConnectionClosed:
                break
            try:
                data = json.loads(data)
                print(json.dumps(data, indent=4))
            except ValueError:
                print(data)


asyncio.get_event_loop().run_until_complete(coindesk())

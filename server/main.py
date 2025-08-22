# server/main.py
import sys
from cryptography.hazmat.primitives import serialization
import asyncio
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from socketserver import (
    BaseRequestHandler,
    StreamRequestHandler,
    ThreadingTCPServer,
    ThreadingMixIn
)
from kalshi_client import Environment
from server_internal_dtypes import Auth_Kalshi, Endpoint
from websocket_handlers import kalshi_ws_handler, polymarket_ws_handler
from threading import Thread
import json
from orderbook_ext import ServerState


async def main():
    # print("Checking External Endpoints")
    # endpoints = get_markets(from_file="markets.json")

    # print("Initializing Internal State")
    # init_globals(markets = endpoints)

    # async with asyncio.TaskGroup() as tg:
    #     print("Spawning Endpoint Listener Thread")
    #     task1 = spawn_extern_listener(endpoints=endpoints)

    #     print("Spawning Client Listener Thread")
    #     clients = []
    #     task2 = tg.create_task(spawn_client_listener(clients))

    # Initialize the WebSocket client
    load_dotenv()
    env = Environment.PROD # toggle environment here
    KEYID = os.getenv('DEMO_KEYID', '') if env == Environment.DEMO else os.getenv('PROD_KEYID', '')
    KEYFILE = os.getenv('DEMO_KEYFILE', '') if env == Environment.DEMO else os.getenv('PROD_KEYFILE', '')
    try:
        with open(KEYFILE, "rb") as key_file: #type: ignore
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None  # Provide the password if your key is encrypted
            )
            print(private_key)
    except FileNotFoundError:
        raise FileNotFoundError(f"Private key file not found at {KEYFILE}")
    except Exception as e:
        raise Exception(f"Error loading private key: {str(e)}")
    ws_client_auth = Auth_Kalshi(
        keyid=KEYID,
        private_key=private_key, # type: ignore
        env=env
    )
    marks = []
    if len(sys.argv) <= 1:
        print("invalid arguments to main, must be > 1 cmd arugment ex: 'kalshi <id>' or 'poly <id>'")
        return
    if 'poly' in sys.argv:
        to_idx = sys.argv.index('kalshi') if 'kalshi' in sys.argv else len(sys.argv)
        ids = sys.argv[sys.argv.index('poly')+1:to_idx]
        marks.extend([Endpoint(description=None,group_id=None,market_name=None,token_id=None, exchange_id='polymarket', market_id=m) for m in ids])
    if 'kalshi' in sys.argv:
        to_idx = sys.argv.index('poly') if 'poly' in sys.argv else len(sys.argv)
        ids = sys.argv[sys.argv.index('kalshi')+1:to_idx]
        marks.extend([Endpoint(description=None,group_id=None,market_name=None,token_id=None, exchange_id='kalshi', market_id=m) for m in ids])
    # Connect via WebSocket
    stuff = [
        kalshi_ws_handler(auth=ws_client_auth, market_tickers=marks),
        # polymarket_ws_handler(market_tickers=marks),
        _showstate(marks)
        ]

    await asyncio.gather(*stuff)
    # print("Server Done, Cleaning up")

async def _showstate(markets):
    s = ServerState()
    while True:
        await asyncio.sleep(1)
        os.system("clear")
        sys.stdout.flush()
        # sys.stdout.write((s.__repr__()))
        for mark in markets:
            sys.stdout.write((str(s.get_market(mark.exchange_id, mark.market_id))))


if __name__ == "__main__":
    asyncio.run(main())

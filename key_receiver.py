import asyncio
import json
import time
import websockets
import keyboard

SERVER_URL = "wss://gift-system.onrender.com/ws?token=nezusystemde"

async def handle_messages():
    print("Connecting to", SERVER_URL)
    while True:
        try:
            async with websockets.connect(SERVER_URL) as ws:
                print("Connected. Waiting for commands...")
                await ws.send("hello")

                while True:
                    data = await ws.recv()
                    try:
                        msg = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    if msg.get("type") == "press":
                        key = msg.get("key")
                        duration_ms = int(msg.get("duration_ms", 50))
                        print(f"Pressing key: {key} for {duration_ms}ms")

                        try:
                            keyboard.press(key)
                            time.sleep(duration_ms / 1000.0)
                            keyboard.release(key)
                        except Exception as e:
                            print("Error pressing key:", e)

        except Exception as e:
            print("Connection error:", e)
            print("Reconnecting in 3 seconds...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(handle_messages())
    except KeyboardInterrupt:
        print("Exiting.")

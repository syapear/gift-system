import json
import os
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

SECRET_TOKEN = os.getenv("GIFT_HUB_TOKEN", "nezusystemde")

# ==============================
# キルカウント（追加部分）
# ==============================
kill_count = 0


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        data = json.dumps(message)
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)


manager = ConnectionManager()

# -----------------------------------------------------
# CORS
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------
# 🌈 ルート（OBS用・虹色キル表示）
# -----------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def kill_overlay():
    global kill_count
    return f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="1">
        <style>
            body {{
                background: rgba(0,0,0,0);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}

            .rainbow {{
                font-size: 120px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                animation: rainbow 3s linear infinite;
            }}

            @keyframes rainbow {{
                0%   {{ color: red; }}
                16%  {{ color: orange; }}
                32%  {{ color: yellow; }}
                48%  {{ color: green; }}
                64%  {{ color: cyan; }}
                80%  {{ color: blue; }}
                100% {{ color: violet; }}
            }}
        </style>
    </head>
    <body>
        <div class="rainbow">{kill_count}</div>
    </body>
    </html>
    """


# -----------------------------------------------------
# + / - キル追加
# -----------------------------------------------------
@app.get("/add", response_class=PlainTextResponse)
def add(value: int = Query(...)):
    global kill_count
    kill_count += value
    return str(kill_count)


# -----------------------------------------------------
# リセット
# -----------------------------------------------------
@app.get("/reset", response_class=PlainTextResponse)
def reset():
    global kill_count
    kill_count = 0
    return "0"


# -----------------------------------------------------
# 既存：テスト用HTML
# -----------------------------------------------------
@app.get("/gift-tester.html", response_class=HTMLResponse)
def gift_tester():
    with open("gift-tester.html", "r", encoding="utf-8") as f:
        return f.read()


# -----------------------------------------------------
# 既存：ギフト受付（キー操作）
# -----------------------------------------------------
@app.post("/gift")
async def gift(
    token: str = Query(...),
    key: str = Query(...),
    duration_ms: int = Query(50)
):
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    key = key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="Key is empty")

    if len(key) != 1:
        raise HTTPException(status_code=400, detail="Key must be 1 char")

    payload = {
        "type": "press",
        "key": key,
        "duration_ms": duration_ms,
    }

    await manager.broadcast(payload)
    return {"status": "ok", "sent_to": len(manager.active_connections)}


# -----------------------------------------------------
# 既存：WebSocket
# -----------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    if token != SECRET_TOKEN:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# -----------------------------------------------------
# Render 用の起動
# -----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

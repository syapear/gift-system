import json
import os
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

SECRET_TOKEN = os.getenv("GIFT_HUB_TOKEN", "nezusystemde")

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
# CORS (必須)
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------
# ルート
# -----------------------------------------------------

@app.get("/", response_class=PlainTextResponse)
def root():
    return "GiftHub server is running."

# 追加した HTML 返却ルート（ここが重要）
@app.get("/gift-tester.html", response_class=HTMLResponse)
def gift_tester():
    with open("gift-tester.html", "r", encoding="utf-8") as f:
        return f.read()

# ギフト受付
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

# WebSocket
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
# Render 用の起動コード
# -----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

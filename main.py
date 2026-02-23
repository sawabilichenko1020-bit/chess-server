from fastapi import FastAPI, WebSocket
from typing import List

app = FastAPI()

# Список активных подключений (игроков)
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str, sender: WebSocket):
        # Рассылаем ход всем, кроме того, кто его сделал
        for connection in self.active_connections:
            if connection != sender:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/game_1")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Ждем ход от игрока
            data = await websocket.receive_text()
            # Пересылаем его второму игроку
            await manager.broadcast(data, websocket)
    except Exception:
        manager.disconnect(websocket)
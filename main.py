from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        # Теперь это словарь: { "номер_комнаты": [список_игроков] }
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        # Если такой комнаты еще нет — создаем её
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        # Удаляем игрока из конкретной комнаты
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
            # Если в комнате никого не осталось — удаляем саму комнату
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, message: str, room_id: str, sender: WebSocket):
        # Рассылаем ход только тем, кто сидит в этой же комнате
        if room_id in self.rooms:
            for connection in self.rooms[room_id]:
                if connection != sender:
                    await connection.send_text(message)

manager = ConnectionManager()

# Теперь адрес выглядит так: /ws/название_комнаты
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Пересылаем данные именно в ту комнату, откуда они пришли
            await manager.broadcast(data, room_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = FastAPI()

# --- Логика шахматных комнат ---
class ConnectionManager:
    def __init__(self):
        self.rooms = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, message: str, room_id: str, sender: WebSocket):
        if room_id in self.rooms:
            for connection in self.rooms[room_id]:
                if connection != sender:
                    await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, room_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

# --- Настройка Telegram Бота ---
# ВСТАВЬ СВОЙ ТОКЕН НИЖЕ
TOKEN = "8760930148:AAFZULQP8zgNRTUwoWvbhX-atxuKz1CxqEA" 
BOT_USERNAME = "me_chess_bot" # Твое имя бота без @

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Используем ID чата как уникальный номер комнаты
    chat_id = update.effective_chat.id
    # Создаем ссылку. Мы убираем минус из ID чата, если он там есть
    room_id = str(chat_id).replace("-", "")
    link = f"https://t.me/{BOT_USERNAME}/coolchess?startapp={room_id}"
    
    await update.message.reply_text(
        f"♟ **Шахматная партия готова!**\n\n"
        f"Нажмите на кнопку ниже, чтобы войти в игру. "
        f"Первые двое зашедших станут соперниками!\n\n"
        f"🔗 [ИГРАТЬ]({link})",
        parse_mode="Markdown"
    )

# Запуск фоновых процессов бота при старте сервера
@app.on_event("startup")
async def start_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("play", play))
    
    # Инициализируем и запускаем бота "в фоне"
    await application.initialize()
    await application.start()
    asyncio.create_task(application.updater.start_polling())
    print("Бот запущен и готов к работе в чатах!")

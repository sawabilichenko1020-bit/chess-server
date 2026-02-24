import os
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = FastAPI()

# Хранилище комнат: {room_id: {"players": {user_id: {"color": "w", "name": "Ivan"}}, "sockets": []}}
rooms = {}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    user_id = websocket.query_params.get("user_id")
    user_name = websocket.query_params.get("name", "Аноним")
    
    await websocket.accept()
    
    if room_id not in rooms:
        rooms[room_id] = {"players": {}, "sockets": []}
    
    # Назначаем роль
    room = rooms[room_id]
    if user_id not in room["players"]:
        if len(room["players"]) == 0:
            room["players"][user_id] = {"color": "w", "name": user_name}
        elif len(room["players"]) == 1:
            room["players"][user_id] = {"color": "b", "name": user_name}
        else:
            room["players"][user_id] = {"color": "viewer", "name": user_name}

    my_role = room["players"][user_id]["color"]
    room["sockets"].append(websocket)

    # Отправляем игроку его роль и данные о противнике
    await websocket.send_text(json.dumps({
        "type": "init",
        "role": my_role,
        "players": room["players"]
    }))

    try:
        while True:
            data = await websocket.receive_text()
            # Пересылаем сообщение всем остальным в комнате
            for client in room["sockets"]:
                if client != websocket:
                    await client.send_text(data)
    except WebSocketDisconnect:
        room["sockets"].remove(websocket)

# --- Бот для команд /play и /duel ---
TOKEN = "8760930148:AAFZULQP8zgNRTUwoWvbhX-atxuKz1CxqEA"
BOT_USERNAME = "me_chess_bot"

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    room_id = update.effective_chat.id
    link = f"https://t.me/{BOT_USERNAME}/coolchess?startapp={room_id}"
    await update.message.reply_text(f"♟ **Игра в шахматы!**\nЗаходи: {link}", parse_mode="Markdown")

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пиши: /duel @ник")
        return
    opponent = context.args[0]
    room_id = f"duel_{update.effective_user.id}"
    link = f"https://t.me/{BOT_USERNAME}/coolchess?startapp={room_id}"
    await update.message.reply_text(f"⚔️ {update.effective_user.first_name} вызывает {opponent}!\nПринять вызов: {link}")

@app.on_event("startup")
async def start_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("duel", duel))
    await application.initialize()
    await application.start()
    asyncio.create_task(application.updater.start_polling())


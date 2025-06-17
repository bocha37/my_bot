import os
import asyncio
import threading
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from http.server import BaseHTTPRequestHandler, HTTPServer

# === Твой бот ===
from config import BOT_TOKEN

# Роутеры будут подключены из handlers
async def run_aiogram_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры
    from handlers import start, callbacks
    dp.include_router(start.router)
    dp.include_router(callbacks.router)

    # Удаляем вебхук, если был установлен
    await bot.delete_webhook(drop_pending_updates=True)

    # Запуск бота
    await dp.start_polling(bot)

# === Минимальный HTTP-сервер для Render ===
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running...")

def run_http_server():
    port = int(os.getenv("PORT", 8000))
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"HTTP Server запущен на порту {port}")
    httpd.serve_forever()

# === Основной запуск ===
if __name__ == "__main__":
    # Запускаем HTTP-сервер в отдельном потоке
    http_thread = threading.Thread(target=run_http_server)
    http_thread.daemon = True
    http_thread.start()

    # В основном потоке запускаем Telegram-бота
    asyncio.run(run_aiogram_bot())
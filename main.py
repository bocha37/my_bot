import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры
    from handlers import callbacks, start
    dp.include_router(start.router)
    dp.include_router(callbacks.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
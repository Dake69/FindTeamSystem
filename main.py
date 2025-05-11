import logging
from aiogram import Bot, Dispatcher
import asyncio

from database.db import test_connection

from config import *

from handlers.reg import router as reg_router

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    await test_connection()
    logging.basicConfig(level=logging.INFO)

    dp.include_router(reg_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

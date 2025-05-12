import logging
from aiogram import Bot, Dispatcher
import asyncio

from database.db import test_connection

from config import *

from handlers.reg import router as reg_router
from handlers.admin.admin import router as admin_router
from handlers.slider import router as slider_router

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    await test_connection()
    logging.basicConfig(level=logging.INFO)

    dp.include_router(reg_router)
    dp.include_router(slider_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

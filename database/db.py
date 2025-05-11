from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI
import asyncio

client = AsyncIOMotorClient(MONGODB_URI)
db = client.get_default_database()

async def test_connection():
    try:
        await db.command("ping")
        print("✅ Успешное подключение к MongoDB!")
    except Exception as e:
        print(f"❌ Ошибка подключения к MongoDB: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
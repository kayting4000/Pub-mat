from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    return _client[settings.MONGO_DB_NAME]


async def connect_mongo():
    global _client
    _client = AsyncIOMotorClient(settings.MONGO_URL)


async def close_mongo():
    if _client:
        _client.close()

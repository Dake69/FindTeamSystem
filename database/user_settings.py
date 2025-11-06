from database.db import db

settings_collection = db.user_settings


async def add_settings(user_id):
    existing = await settings_collection.find_one({"user_id": user_id})
    if existing:
        return existing
    doc = {
        "user_id": user_id,
        "notify_on_like": True,
        "notify_on_match": True,
        "notify_sound": True
    }
    result = await settings_collection.insert_one(doc)
    return await settings_collection.find_one({"_id": result.inserted_id})


async def get_settings_by_user(user_id):
    return await settings_collection.find_one({"user_id": user_id})


async def update_settings(user_id, update_data: dict):
    result = await settings_collection.update_one({"user_id": user_id}, {"$set": update_data})
    return result.modified_count > 0


async def ensure_settings(user_id):
    settings = await get_settings_by_user(user_id)
    if not settings:
        settings = await add_settings(user_id)
    return settings

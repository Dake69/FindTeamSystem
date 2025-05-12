from database.db import db
from bson import ObjectId

languages_collection = db.languages

async def add_language(name, code=None):
    language = {"name": name}
    if code:
        language["code"] = code
    result = await languages_collection.insert_one(language)
    return str(result.inserted_id)

async def get_language_by_id(language_id):
    return await languages_collection.find_one({"_id": ObjectId(language_id)})

async def get_all_languages():
    cursor = languages_collection.find({})
    return [lang async for lang in cursor]

async def update_language(language_id, update_data: dict):
    result = await languages_collection.update_one(
        {"_id": ObjectId(language_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0

async def delete_language(language_id):
    result = await languages_collection.delete_one({"_id": ObjectId(language_id)})
    return result.deleted_count > 0
from database.db import db
from bson import ObjectId

filters_collection = db.filters


async def add_filter(user_id):
    filter_doc = {
        "user_id": user_id,
        "games": [],
        "gender": "any",
        "age_min": None,
        "age_max": None,
        "games_ranks": {}
    }
    result = await filters_collection.insert_one(filter_doc)
    return str(result.inserted_id)


async def get_filter_by_user(user_id):
    return await filters_collection.find_one({"user_id": user_id})


async def update_filter(user_id, update_data: dict):
    result = await filters_collection.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    return result.modified_count > 0


async def delete_filter(user_id):
    result = await filters_collection.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def get_all_filters():
    cursor = filters_collection.find({})
    return await cursor.to_list(length=None)


async def reset_filter(user_id):
    filter_doc = {
        "games": [],
        "gender": "any",
        "age_min": None,
        "age_max": None,
        "games_ranks": {}
    }
    result = await filters_collection.update_one(
        {"user_id": user_id},
        {"$set": filter_doc}
    )
    return result.modified_count > 0
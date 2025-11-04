from database.db import db
from datetime import datetime

matches_collection = db.matches


async def create_match(user_id_1, user_id_2, game_name):
    existing = await matches_collection.find_one({
        "$or": [
            {"user_id_1": user_id_1, "user_id_2": user_id_2},
            {"user_id_1": user_id_2, "user_id_2": user_id_1}
        ],
        "status": "pending"
    })
    
    if existing:
        return None
    
    match_data = {
        "user_id_1": user_id_1,
        "user_id_2": user_id_2,
        "game_name": game_name,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "matched_at": None
    }
    
    result = await matches_collection.insert_one(match_data)
    return await matches_collection.find_one({"_id": result.inserted_id})


async def get_match_by_id(match_id):
    return await matches_collection.find_one({"_id": match_id})


async def get_user_matches(user_id, skip=0, limit=50):
    query = {"$or": [{"user_id_1": user_id}, {"user_id_2": user_id}]}
    cursor = matches_collection.find(query).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def accept_match(match_id):
    result = await matches_collection.update_one(
        {"_id": match_id},
        {"$set": {"status": "accepted", "matched_at": datetime.utcnow()}}
    )
    return result.modified_count > 0


async def reject_match(match_id):
    result = await matches_collection.update_one(
        {"_id": match_id},
        {"$set": {"status": "rejected"}}
    )
    return result.modified_count > 0


async def get_accepted_matches(user_id):
    query = {
        "$or": [{"user_id_1": user_id}, {"user_id_2": user_id}],
        "status": "accepted"
    }
    cursor = matches_collection.find(query)
    return await cursor.to_list(length=None)

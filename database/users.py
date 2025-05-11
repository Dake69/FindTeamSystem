from database.db import db

users_collection = db.users

async def add_user(user_id, full_name, nickname, phone, games, username):
    existing = await users_collection.find_one({
        "$or": [
            {"user_id": user_id},
            {"phone": phone},
            {"nickname": nickname}
        ]
    })
    if existing:
        return {"success": False, "reason": "Пользователь уже существует"}
    
    if not isinstance(games, list):
        games = [games]

    user_data = {
        "user_id": user_id,
        "full_name": full_name,
        "nickname": nickname,
        "phone": phone,
        "games": games,
        "username": username
    }
    await users_collection.insert_one(user_data)
    return {"success": True}

async def get_user_by_id(user_id):
    user = await users_collection.find_one({"user_id": user_id})
    return user

async def get_user_by_phone(phone):
    return await users_collection.find_one({"phone": phone})

async def get_user_by_nickname(nickname):
    return await users_collection.find_one({"nickname": nickname})
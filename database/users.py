from database.db import db

users_collection = db.users

async def add_user(
    user_id,
    full_name,
    nickname,
    age,
    gender,
    about,
    phone,
    games_with_ranks,
    username,
    language

):
    existing = await users_collection.find_one({
        "$or": [
            {"user_id": user_id},
            {"phone": phone},
            {"nickname": nickname}
        ]
    })
    if existing:
        return {"success": False, "reason": "Пользователь уже существует"}

    user_data = {
        "user_id": user_id,
        "full_name": full_name,
        "nickname": nickname,
        "age": age,
        "gender": gender,
        "about": about,
        "phone": phone,
        "games": games_with_ranks,
        "username": username,
        "language": language

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
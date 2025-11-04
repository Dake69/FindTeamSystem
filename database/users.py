from database.db import db

users_collection = db.users


async def add_user(
    user_id,
    full_name,
    nickname,
    age,
    gender,
    about,
    photo_id,
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
        "photo_id": photo_id,
        "phone": phone,
        "games": games_with_ranks,
        "username": username,
        "language": language,
        "is_active": True
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


async def get_all_active_users(skip=0, limit=100):
    cursor = users_collection.find({"is_active": True}).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def get_users_by_game(game_name, skip=0, limit=100):
    query = {f"games.{game_name}": {"$exists": True}, "is_active": True}
    cursor = users_collection.find(query).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def update_user(user_id, update_data):
    """Обновляет данные пользователя"""
    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

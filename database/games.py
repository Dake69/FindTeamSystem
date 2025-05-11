from database.db import db
from bson import ObjectId

games_collection = db.games
genres_collection = db.genres

async def add_game(game_name, genre=None, description=None, ranks=None):
    existing = await games_collection.find_one({"game_name": game_name})
    if existing:
        return {"success": False, "reason": "Игра уже существует"}
    
    if not isinstance(ranks, list):
        ranks = [ranks] if ranks else []

    game_data = {
        "game_name": game_name,
        "genre": genre,
        "description": description,
        "ranks": ranks
    }
    await games_collection.insert_one(game_data)
    return {"success": True}

async def get_game_by_name(game_name):
    return await games_collection.find_one({"game_name": game_name})

async def get_game_by_id(game_id):
    return await games_collection.find_one({"_id": game_id})

async def get_all_games():
    cursor = games_collection.find({})
    return [game async for game in cursor]

async def delete_game(game_id):
    print("Удаляем игру с id:", game_id)
    if not isinstance(game_id, ObjectId):
        game_id = ObjectId(game_id)
    result = await games_collection.delete_one({"_id": game_id})
    return result.deleted_count > 0

async def update_game(game_id, update_data):
    if not isinstance(game_id, ObjectId):
        game_id = ObjectId(game_id)
    result = await games_collection.update_one(
        {"_id": game_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

#---------------------------------------------------------------------------------------------------

async def add_genre(name, description=None):
    existing = await genres_collection.find_one({"name": name})
    if existing:
        return {"success": False, "reason": "Жанр уже существует"}
    genre_data = {
        "name": name,
        "description": description or ""
    }
    await genres_collection.insert_one(genre_data)
    return {"success": True}

async def get_genre_by_name(name):
    return await genres_collection.find_one({"name": name})

async def get_genre_by_id(genre_id):
    if not isinstance(genre_id, ObjectId):
        genre_id = ObjectId(genre_id)
    return await genres_collection.find_one({"_id": genre_id})

async def get_all_genres():
    cursor = genres_collection.find({})
    return [genre async for genre in cursor]

async def update_genre(genre_id, update_data):
    if not isinstance(genre_id, ObjectId):
        genre_id = ObjectId(genre_id)
    result = await genres_collection.update_one(
        {"_id": genre_id},
        {"$set": update_data}
    )
    return result.modified_count > 0

async def delete_genre(genre_id):
    if not isinstance(genre_id, ObjectId):
        genre_id = ObjectId(genre_id)
    result = await genres_collection.delete_one({"_id": genre_id})
    return result.deleted_count > 0
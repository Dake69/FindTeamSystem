from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

game_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Game 1", callback_data="game_1")],
    [InlineKeyboardButton(text="Game 2", callback_data="game_2")],
])

def get_games_keyboard(selected_games):

    GAMES = [
        "CS:GO",
        "Dota 2",
        "PUBG",
        "Valorant",
        "Apex Legends",
        "League of Legends",
        "Fortnite",
        "Overwatch",
        "Rainbow Six Siege",
        "Call of Duty"
    ]
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if game in selected_games else ''} {game}",
                callback_data=f"game_{game}"
            )
        ] for game in GAMES
    ]
    buttons.append([InlineKeyboardButton(text="🎯 Готово", callback_data="games_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


contact_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Share contact", request_contact=True)],
], resize_keyboard=True, one_time_keyboard=True)

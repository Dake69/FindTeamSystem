from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.games import get_all_games

game_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Game 1", callback_data="game_1")],
    [InlineKeyboardButton(text="Game 2", callback_data="game_2")],
])

async def get_games_keyboard(selected_games):
    games = await get_all_games()
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if game.get('game_name') in selected_games else ''} {game.get('game_name')}",
                callback_data=f"game_{game.get('game_name')}"
            )
        ] for game in games
    ]
    buttons.append([InlineKeyboardButton(text="🎯 Готово", callback_data="games_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


contact_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Share contact", request_contact=True)],
], resize_keyboard=True, one_time_keyboard=True)

main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📰 Лента", callback_data="feed"),
            InlineKeyboardButton(text="👤 Личный кабинет", callback_data="profile")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        ]
    ]
)

main_menu_inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
)
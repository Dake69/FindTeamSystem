from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.games import get_all_games, get_game_by_name



settings_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔎 Настроить фильтры", callback_data="settings_filters")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="settings_statistics")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")],
    ]
)

def get_age_filter_keyboard(selected_ranges):

    AGE_RANGES = [
    ("10-19", [10, 19]),
    ("20-29", [20, 29]),
    ("30-39", [30, 39]),
    ("40-49", [40, 49]),
    ("50-59", [50, 59]),
    ("60+", [60, 120]),
    ]


    keyboard = [
        [
            InlineKeyboardButton(
                text=("✅ " if age_range in selected_ranges else "") + label,
                callback_data=f"toggle_age_{label}"
            )
        ] for label, age_range in AGE_RANGES
    ]
    keyboard.append([InlineKeyboardButton(text="🎯 Готово", callback_data="age_done")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_filter")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_filter_games_keyboard(selected_games):
    from database.games import get_all_games
    all_games = await get_all_games()
    keyboard = []
    for game in all_games:
        name = game["game_name"]
        text = ("✅ " if name in selected_games else "") + name
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"filter_game_{name}")])
    keyboard.append([InlineKeyboardButton(text="🎯 Готово", callback_data="filter_games_done")])
    print("selected_games:", selected_games)
    print("all_games:", [g["game_name"] for g in all_games])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_game_filter_type_kb(game_name):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Только игру", callback_data=f"filter_game_only_{game_name}")],
            [InlineKeyboardButton(text="🏆 По рангу", callback_data=f"filter_game_rank_{game_name}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_filter_games")]
        ]
    )

def get_ranks_keyboard(game_name, ranks, selected_ranks):
    keyboard = []
    for rank in ranks:
        text = ("✅ " if rank in selected_ranks else "") + rank
        keyboard.append([InlineKeyboardButton(
            text=text,
            callback_data=f"toggle_rank_{rank}"
        )])
    if ranks:
        keyboard.append([InlineKeyboardButton(
            text="Выбрать все ранги",
            callback_data="select_all_ranks"
        )])
    keyboard.append([InlineKeyboardButton(
        text="🎯 Готово",
        callback_data="ranks_done"
    )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
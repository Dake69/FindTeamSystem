from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.games import get_all_games, get_game_by_name



settings_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔎 Настроить фильтры", callback_data="settings_filters")],
    ]
)

async def get_filter_games_keyboard(selected_games):
    games = await get_all_games()
    buttons = [
        [InlineKeyboardButton(
            text=f"{'✅' if g['game_name'] in selected_games else '⬜️'} {g['game_name']}",
            callback_data=f"filter_game_{g['game_name']}"
        )] for g in games
    ]
    buttons.append([InlineKeyboardButton(text="🎯 Готово", callback_data="filter_games_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_game_filter_type_kb(game_name):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Только игру", callback_data=f"filter_game_only_{game_name}")],
            [InlineKeyboardButton(text="🏆 По рангу", callback_data=f"filter_game_rank_{game_name}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_filter_games")]
        ]
    )

def get_ranks_keyboard(game_name, ranks, selected_ranks):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'✅' if rank in selected_ranks else '⬜️'} {rank}",
                callback_data=f"filter_rank_{game_name}_{rank}"
            )] for rank in ranks
        ] + [[InlineKeyboardButton(text="🎯 Готово", callback_data=f"filter_ranks_done_{game_name}")]]
    )
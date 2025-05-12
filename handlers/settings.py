from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from FSM.all import *

from database.filtrs import *
from database.users import *

from keyboards.settings_keyboards import *

router = Router()

@router.callback_query(F.data == "settings")
async def settings_back(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "⚙️ <b>Меню настроек</b>\n\nВыберите, что хотите изменить:",
        parse_mode="HTML",
        reply_markup=settings_kb
    )
    await callback.answer()

@router.callback_query(F.data == "settings_filters")
async def settings_filters_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_filter = await get_filter_by_user(user_id)
    text = "🔎 <b>Ваш текущий фильтр:</b>\n\n"
    if user_filter:
        games = user_filter.get("games", [])
        gender = user_filter.get("gender", "any")
        age = user_filter.get("age", "any")

        games_str = "Не выбрано" if not games else ", ".join(games)
        gender_str = (
            "Любой" if gender == "any" else
            "Мужской" if gender == "male" else
            "Женский" if gender == "female" else gender
        )
        age_str = "Любой" if age == "any" else str(age)

        text += (
            f"🎮 <b>Игры:</b> {games_str}\n"
            f"🧑 <b>Пол:</b> {gender_str}\n"
            f"🎂 <b>Возраст:</b> {age_str}\n"
        )
    else:
        text += "Фильтр не установлен (используются все параметры по умолчанию).\n"

    text += "\nВы можете изменить или сбросить фильтр:"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить фильтр", callback_data="edit_filter")],
            [InlineKeyboardButton(text="🔄 Сбросить фильтр", callback_data="reset_filter")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_back")]
        ]
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "edit_filter")
async def edit_filter_menu(callback: CallbackQuery, state: FSMContext):
    text = (
        "✏️ <b>Изменение фильтра</b>\n\n"
        "Выберите, какой параметр фильтра вы хотите изменить:"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Игры", callback_data="edit_filter_games")],
            [InlineKeyboardButton(text="🧑 Пол", callback_data="edit_filter_gender")],
            [InlineKeyboardButton(text="🎂 Возраст", callback_data="edit_filter_age")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_filters")]
        ]
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()
@router.callback_query(F.data == "edit_filter_games")
async def edit_filter_games_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_filter = await get_filter_by_user(user_id)
    selected_games = user_filter.get("games", []) if user_filter else []
    await state.update_data(games=selected_games, games_ranks=user_filter.get("games_ranks", {}))
    await state.set_state(FilterFSM.games)
    await callback.message.edit_text(
        "Выберите игры для фильтрации (можно несколько):",
        reply_markup=await get_filter_games_keyboard(selected_games),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(FilterFSM.games)
async def edit_filter_choose_games(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_games = data.get("games", [])
    games_ranks = data.get("games_ranks", {})
    if callback.data.startswith("filter_game_"):
        game = callback.data[12:]
        if game in selected_games:
            selected_games.remove(game)
            games_ranks.pop(game, None)
        else:
            selected_games.append(game)
        await state.update_data(games=selected_games, games_ranks=games_ranks)
        await callback.message.edit_text(
            "Выберите игры для фильтрации (можно несколько):",
            reply_markup=await get_filter_games_keyboard(selected_games),
            parse_mode="HTML"
        )
        await callback.answer()
    elif callback.data == "filter_games_done":
        if not selected_games:
            await callback.answer("Выберите хотя бы одну игру!", show_alert=True)
            return
        await state.set_state(FilterFSM.ranks)
        await callback.message.edit_text(
            "Выберите игру, чтобы настроить фильтрацию по рангу или оставить только по игре:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=game, callback_data=f"choose_game_filter_{game}")]
                    for game in selected_games
                ] + [[InlineKeyboardButton(text="🎯 Готово", callback_data="filter_games_final")]]
            ),
            parse_mode="HTML"
        )
        await callback.answer()

@router.callback_query(FilterFSM.ranks)
async def edit_filter_choose_game_filter(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    games = data.get("games", [])
    games_ranks = data.get("games_ranks", {})
    if callback.data.startswith("choose_game_filter_"):
        game_name = callback.data.replace("choose_game_filter_", "")
        await callback.message.edit_text(
            f"Что фильтровать в игре <b>{game_name}</b>?",
            parse_mode="HTML",
            reply_markup=get_game_filter_type_kb(game_name)
        )
        await callback.answer()
    elif callback.data.startswith("filter_game_only_"):
        game_name = callback.data.replace("filter_game_only_", "")
        games_ranks[game_name] = []
        await state.update_data(games_ranks=games_ranks)
        await callback.message.edit_text(
            "Выберите игру, чтобы настроить фильтрацию по рангу или оставить только по игре:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=game, callback_data=f"choose_game_filter_{game}")]
                    for game in games
                ] + [[InlineKeyboardButton(text="🎯 Готово", callback_data="filter_games_final")]]
            ),
            parse_mode="HTML"
        )
        await callback.answer()
    elif callback.data.startswith("filter_game_rank_"):
        game_name = callback.data.replace("filter_game_rank_", "")
        game = await get_game_by_name(game_name)
        ranks = game.get("ranks", [])
        selected_ranks = data.get("games_ranks", {}).get(game_name, [])
        await callback.message.edit_text(
            f"Выберите ранги для игры <b>{game_name}</b> (можно несколько):",
            parse_mode="HTML",
            reply_markup=get_ranks_keyboard(game_name, ranks, selected_ranks)
        )
        await callback.answer()
    elif callback.data.startswith("filter_rank_"):
        _, game_name, rank = callback.data.split("_", 2)
        games_ranks = data.get("games_ranks", {})
        selected_ranks = games_ranks.get(game_name, [])
        if rank in selected_ranks:
            selected_ranks.remove(rank)
        else:
            selected_ranks.append(rank)
        games_ranks[game_name] = selected_ranks
        await state.update_data(games_ranks=games_ranks)
        game = await get_game_by_name(game_name)
        ranks = game.get("ranks", [])
        await callback.message.edit_text(
            f"Выберите ранги для игры <b>{game_name}</b> (можно несколько):",
            parse_mode="HTML",
            reply_markup=get_ranks_keyboard(game_name, ranks, selected_ranks)
        )
        await callback.answer()
    elif callback.data.startswith("filter_ranks_done_"):
        await callback.message.edit_text(
            "Выберите игру, чтобы настроить фильтрацию по рангу или оставить только по игре:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=game, callback_data=f"choose_game_filter_{game}")]
                    for game in games
                ] + [[InlineKeyboardButton(text="🎯 Готово", callback_data="filter_games_final")]]
            ),
            parse_mode="HTML"
        )
        await callback.answer()
    elif callback.data == "filter_games_final":
        await update_filter(
            callback.from_user.id,
            {
                "games": games,
                "games_ranks": data.get("games_ranks", {})
            }
        )
        await state.clear()
        await callback.message.edit_text(
            "✅ Фильтр по играм и рангам успешно обновлён!",
            reply_markup=settings_kb,
            parse_mode="HTML"
        )
        await callback.answer()
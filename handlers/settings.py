from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from FSM.all import *

from database.filtrs import *
from database.users import *
from database.games import get_all_games, get_game_by_name

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
        from database.games import get_game_by_name
        existing_games = []
        for game in games:
            if await get_game_by_name(game):
                existing_games.append(game)
        games = existing_games

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
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings")]
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
    all_games = await get_all_games()
    selected_games = user_filter.get("games", []) if user_filter else []
    games_ranks = user_filter.get("games_ranks", {}) if user_filter else {}
    await state.update_data(
        all_games=[g["game_name"] for g in all_games],
        games=selected_games,
        games_ranks=games_ranks,
        current_game_idx=0
    )
    await state.set_state(FilterFSM.games)
    await callback.message.edit_text(
        "Выберите игры, которые вы хотите видеть в ленте (можно несколько):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=("✅ " if g["game_name"] in selected_games else "") + g["game_name"],
                    callback_data=f"toggle_game_{g['game_name']}"
                )] for g in all_games
            ] + [[InlineKeyboardButton(text="🎯 Готово", callback_data="games_selected_done")]]
        ),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(FilterFSM.games)
async def edit_filter_choose_games(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    all_games = data.get("all_games", [])
    selected_games = data.get("games", [])
    games_ranks = data.get("games_ranks", {})
    if callback.data.startswith("toggle_game_"):
        game = callback.data.replace("toggle_game_", "")
        if game in selected_games:
            selected_games.remove(game)
            games_ranks.pop(game, None)
        else:
            selected_games.append(game)
        await state.update_data(games=selected_games, games_ranks=games_ranks)
        await callback.message.edit_text(
            "Выберите игры, которые вы хотите видеть в ленте (можно несколько):",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text=("✅ " if g in selected_games else "") + g,
                        callback_data=f"toggle_game_{g}"
                    )] for g in all_games
                ] + [[InlineKeyboardButton(text="🎯 Готово", callback_data="games_selected_done")]]
            ),
            parse_mode="HTML"
        )
        await callback.answer()
    elif callback.data == "games_selected_done":
        if not selected_games:
            await callback.answer("Выберите хотя бы одну игру!", show_alert=True)
            return
        await state.set_state(FilterFSM.ranks)
        await state.update_data(current_game_idx=0)
        game_name = selected_games[0]
        game = await get_game_by_name(game_name)
        ranks = game.get("ranks", []) if game else []
        await callback.message.edit_text(
            f"Выберите ранги для игры <b>{game_name}</b> (можно несколько):",
            parse_mode="HTML",
            reply_markup=get_ranks_keyboard(game_name, ranks, games_ranks.get(game_name, []))
        )
        await callback.answer()

@router.callback_query(FilterFSM.ranks)
async def edit_filter_choose_ranks(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_games = data.get("games", [])
    games_ranks = data.get("games_ranks", {})
    idx = data.get("current_game_idx", 0)
    game_name = selected_games[idx]
    game = await get_game_by_name(game_name)
    ranks = game.get("ranks", []) if game else []
    selected_ranks = games_ranks.get(game_name, [])

    if callback.data == "select_all_ranks":
        selected_ranks = list(ranks)
        games_ranks[game_name] = selected_ranks
        await state.update_data(games_ranks=games_ranks)
        await callback.message.edit_text(
            f"Выберите ранги для игры <b>{game_name}</b> (можно несколько):",
            parse_mode="HTML",
            reply_markup=get_ranks_keyboard(game_name, ranks, selected_ranks)
        )
        await callback.answer()
        return

    if callback.data.startswith("toggle_rank_"):
        rank = callback.data.replace("toggle_rank_", "")
        if rank in selected_ranks:
            selected_ranks.remove(rank)
        else:
            selected_ranks.append(rank)
        games_ranks[game_name] = selected_ranks
        await state.update_data(games_ranks=games_ranks)
        await callback.message.edit_text(
            f"Выберите ранги для игры <b>{game_name}</b> (можно несколько):",
            parse_mode="HTML",
            reply_markup=get_ranks_keyboard(game_name, ranks, selected_ranks)
        )
        await callback.answer()
        return

    if callback.data == "ranks_done":
        if idx + 1 < len(selected_games):
            next_idx = idx + 1
            next_game = selected_games[next_idx]
            next_game_obj = await get_game_by_name(next_game)
            next_ranks = next_game_obj.get("ranks", []) if next_game_obj else []
            await state.update_data(current_game_idx=next_idx)
            await callback.message.edit_text(
                f"Выберите ранги для игры <b>{next_game}</b> (можно несколько):",
                parse_mode="HTML",
                reply_markup=get_ranks_keyboard(next_game, next_ranks, games_ranks.get(next_game, []))
            )
            await callback.answer()
        else:
            await update_filter(
                callback.from_user.id,
                {
                    "games": selected_games,
                    "games_ranks": games_ranks
                }
            )
            await state.clear()
            await callback.message.edit_text(
                "✅ Фильтр по играм и рангам успешно обновлён!",
                reply_markup=settings_kb,
                parse_mode="HTML"
            )
            await callback.answer()

@router.callback_query(F.data == "reset_filter")
async def reset_filter_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await reset_filter(user_id)
    await state.clear()
    await callback.message.edit_text(
        "🔄 Фильтр сброшен до значений по умолчанию.",
        parse_mode="HTML",
        reply_markup=settings_kb
    )
    await callback.answer()


@router.callback_query(F.data == "edit_filter_gender")
async def edit_filter_gender(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Любой", callback_data="gender_any"),
                InlineKeyboardButton(text="Мужской", callback_data="gender_male"),
                InlineKeyboardButton(text="Женский", callback_data="gender_female"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_filter")]
        ]
    )
    await callback.message.edit_text(
        "🧑 <b>Выберите пол пользователей, которых хотите видеть в поиске:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.in_(["gender_any", "gender_male", "gender_female"]))
async def set_filter_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.replace("gender_", "")
    await update_filter(callback.from_user.id, {"gender": gender})
    await callback.message.edit_text(
        "✅ Фильтр по полу обновлён.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_filters")]
            ]
        )
    )
    await callback.answer()

@router.callback_query(F.data == "edit_filter_age")
async def edit_filter_age(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_filter = await get_filter_by_user(user_id)
    selected_ranges = user_filter.get("age", []) if user_filter and isinstance(user_filter.get("age", []), list) else []
    await state.update_data(age_ranges=selected_ranges)
    await callback.message.edit_text(
        "🎂 <b>Выберите возрастные диапазоны пользователей, которых хотите видеть в поиске:</b>\n\n"
        "Можно выбрать несколько диапазонов.",
        parse_mode="HTML",
        reply_markup=get_age_filter_keyboard(selected_ranges)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_age_"))
async def toggle_age_range(callback: CallbackQuery, state: FSMContext):
    AGE_RANGES = [
    ("10-19", [10, 19]),
    ("20-29", [20, 29]),
    ("30-39", [30, 39]),
    ("40-49", [40, 49]),
    ("50-59", [50, 59]),
    ("60+", [60, 120]),
    ]

    label = callback.data.replace("toggle_age_", "")
    age_range = next((r for l, r in AGE_RANGES if l == label), None)
    data = await state.get_data()
    selected_ranges = data.get("age_ranges", [])
    if age_range in selected_ranges:
        selected_ranges.remove(age_range)
    else:
        selected_ranges.append(age_range)
    await state.update_data(age_ranges=selected_ranges)
    await callback.message.edit_text(
        "🎂 <b>Выберите возрастные диапазоны пользователей, которых хотите видеть в поиске:</b>\n\n"
        "Можно выбрать несколько диапазонов.",
        parse_mode="HTML",
        reply_markup=get_age_filter_keyboard(selected_ranges)
    )
    await callback.answer()

@router.callback_query(F.data == "age_done")
async def set_filter_age(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_ranges = data.get("age_ranges", [])
    if selected_ranges:
        min_age = min(r[0] for r in selected_ranges)
        max_age = max(r[1] for r in selected_ranges)
        age_filter = [min_age, max_age]
    else:
        age_filter = "any"
    await update_filter(callback.from_user.id, {"age": age_filter})
    await callback.message.edit_text(
        "✅ Фильтр по возрасту обновлён.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_filters")]
            ]
        )
    )
    await callback.answer()

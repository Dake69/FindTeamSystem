from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from FSM.all import EditProfileFSM

from database.users import users_collection, update_user, get_user_by_nickname, get_user_by_id
from keyboards.reg import get_games_keyboard
from database.games import get_game_by_name

router = Router()


@router.callback_query(F.data == "edit_photo")
async def edit_photo_start(callback: CallbackQuery, state: FSMContext):
    skip_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить фото", callback_data="delete_photo")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_profile")]
        ]
    )
    
    try:
        await callback.message.edit_text(
            "📸 Отправьте новое фото для вашего профиля:",
            parse_mode="HTML",
            reply_markup=skip_kb
        )
    except:
        await callback.message.answer(
            "📸 Отправьте новое фото для вашего профиля:",
            parse_mode="HTML",
            reply_markup=skip_kb
        )
    
    await state.set_state(EditProfileFSM.edit_photo)
    await callback.answer()


@router.message(EditProfileFSM.edit_photo, F.photo)
async def save_new_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    
    result = await users_collection.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"photo_id": photo.file_id}}
    )
    
    if result.modified_count > 0:
        await message.answer(
            "✅ Фото успешно обновлено!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
            ])
        )
    else:
        await message.answer("❌ Ошибка при обновлении фото.")
    
    await state.clear()


@router.callback_query(F.data == "delete_photo")
async def delete_photo(callback: CallbackQuery, state: FSMContext):
    result = await users_collection.update_one(
        {"user_id": callback.from_user.id},
        {"$set": {"photo_id": None}}
    )
    
    if result.modified_count > 0:
        await callback.message.edit_text(
            "✅ Фото удалено из профиля!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
            ])
        )
    else:
        await callback.message.edit_text("❌ Ошибка при удалении фото.")
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit_games")
async def edit_games_start(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_id(callback.from_user.id)
    selected_games = list(user.get("games", {}).keys()) if user else []
    try:
        await callback.message.edit_text(
            "🎮 Выберите игры для вашего профиля (нажимайте по очереди):",
            parse_mode="HTML",
            reply_markup=await get_games_keyboard(selected_games)
        )
    except:
        await callback.message.answer(
            "🎮 Выберите игры для вашего профиля (нажимайте по очереди):",
            parse_mode="HTML",
            reply_markup=await get_games_keyboard(selected_games)
        )
    await state.update_data(games=selected_games, games_with_ranks={})
    await state.set_state(EditProfileFSM.edit_games)
    await callback.answer()


@router.callback_query(EditProfileFSM.edit_games)
async def edit_games_toggle(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_games = data.get("games", [])

    if callback.data.startswith("game_"):
        game = callback.data[5:]
        if game in selected_games:
            selected_games.remove(game)
        else:
            selected_games.append(game)
        await state.update_data(games=selected_games)
        await callback.message.edit_text(
            "🎮 Выберите игры для вашего профиля (нажимайте по очереди):",
            parse_mode="HTML",
            reply_markup=await get_games_keyboard(selected_games)
        )
        await callback.answer()
        return

    if callback.data == "games_done":
        if not selected_games:
            await callback.answer("Выберите хотя бы одну игру!", show_alert=True)
            return
        await state.update_data(games_with_ranks={})
        await state.set_state(EditProfileFSM.edit_rank)
        # start asking ranks for first game
        await ask_edit_game_rank(callback, state, 0)
        return

    await callback.answer()


async def ask_edit_game_rank(callback, state: FSMContext, game_idx: int):
    data = await state.get_data()
    games = data.get("games", [])
    if game_idx >= len(games):
        # finished selecting ranks
        await callback.message.edit_text("✅ Выбор игр завершён. Сохраняем...", parse_mode="HTML")
        return

    game_name = games[game_idx]
    game = await get_game_by_name(game_name)
    ranks = game.get("ranks", []) if game else []

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=rank, callback_data=f"edit_rank_{game_idx}_{rank}")]
            for rank in ranks
        ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_profile")]]
    )

    try:
        await callback.message.edit_text(
            f"🏆 Выберите ваш ранг в игре <b>{game_name}</b>:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except:
        await callback.message.answer(
            f"🏆 Выберите ваш ранг в игре <b>{game_name}</b>:",
            parse_mode="HTML",
            reply_markup=keyboard
        )


@router.callback_query(EditProfileFSM.edit_rank, F.data.startswith("edit_rank_"))
async def edit_rank_selected(callback: CallbackQuery, state: FSMContext):
    # callback.data format: edit_rank_{game_idx}_{rank}
    payload = callback.data[len("edit_rank_"):]
    parts = payload.split("_", 1)
    if len(parts) < 2:
        await callback.answer("Ошибка выбора ранга.", show_alert=True)
        return
    game_idx_str, rank = parts[0], parts[1]
    try:
        game_idx = int(game_idx_str)
    except ValueError:
        await callback.answer("Ошибка выбора ранга.", show_alert=True)
        return

    data = await state.get_data()
    games = data.get("games", [])
    games_with_ranks = data.get("games_with_ranks", {})

    if game_idx >= len(games):
        await callback.answer("Ошибка выбора игры.", show_alert=True)
        return

    game_name = games[game_idx]
    games_with_ranks[game_name] = rank
    await state.update_data(games_with_ranks=games_with_ranks)

    # move to next game or finish
    if game_idx + 1 < len(games):
        await ask_edit_game_rank(callback, state, game_idx + 1)
    else:
        # save to DB
        ok = await update_user(callback.from_user.id, {"games": games_with_ranks})
        if ok:
            await callback.message.edit_text("✅ Игры успешно обновлены!", parse_mode="HTML",
                                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                 [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
                                             ]))
        else:
            await callback.message.edit_text("❌ Ошибка при сохранении игр.", parse_mode="HTML")
        await state.clear()
    await callback.answer()


# --- New handlers: edit fullname, nickname and about ---
@router.callback_query(F.data == "edit_fullname")
async def edit_fullname_start(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "📝 Отправьте новое <b>имя</b>:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_profile")]
            ])
        )
    except:
        await callback.message.answer("📝 Отправьте новое <b>имя</b>:", parse_mode="HTML")
    await state.set_state(EditProfileFSM.edit_fullname)
    await callback.answer()


@router.message(EditProfileFSM.edit_fullname, F.text)
async def save_fullname(message: Message, state: FSMContext):
    new_name = message.text.strip()
    if not new_name or len(new_name) < 2:
        await message.answer("❗️ Введите корректное имя (минимум 2 символа).")
        return

    ok = await update_user(message.from_user.id, {"full_name": new_name})
    if ok:
        await message.answer("✅ Имя успешно обновлено!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
        ]))
    else:
        await message.answer("❌ Ошибка при обновлении имени.")

    await state.clear()


@router.callback_query(F.data == "edit_nickname")
async def edit_nickname_start(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "🏷️ Отправьте новый <b>никнейм</b> (без пробелов):",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_profile")]
            ])
        )
    except:
        await callback.message.answer("🏷️ Отправьте новый <b>никнейм</b>:", parse_mode="HTML")
    await state.set_state(EditProfileFSM.edit_nickname)
    await callback.answer()


@router.message(EditProfileFSM.edit_nickname, F.text)
async def save_nickname(message: Message, state: FSMContext):
    new_nick = message.text.strip()
    if not new_nick or " " in new_nick or len(new_nick) < 2:
        await message.answer("❗️ Неверный никнейм. Ник не должен содержать пробелов и должен быть минимум 2 символа.")
        return

    existing = await get_user_by_nickname(new_nick)
    if existing and existing.get("user_id") != message.from_user.id:
        await message.answer("❗️ Такой никнейм уже используется другим пользователем. Выберите другой.")
        return

    ok = await update_user(message.from_user.id, {"nickname": new_nick})
    if ok:
        await message.answer("✅ Никнейм успешно обновлён!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
        ]))
    else:
        await message.answer("❌ Ошибка при обновлении никнейма.")

    await state.clear()


@router.callback_query(F.data == "edit_about")
async def edit_about_start(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "📝 Отправьте новое <b>био</b> (коротко о себе):",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="edit_profile")]
            ])
        )
    except:
        await callback.message.answer("📝 Отправьте новое <b>био</b>:", parse_mode="HTML")
    await state.set_state(EditProfileFSM.edit_about)
    await callback.answer()


@router.message(EditProfileFSM.edit_about, F.text)
async def save_about(message: Message, state: FSMContext):
    new_about = message.text.strip()
    if not new_about:
        await message.answer("❗️ Био не может быть пустым.")
        return
    if len(new_about) > 1000:
        await message.answer("❗️ Слишком длинное био (максимум 1000 символов).")
        return

    ok = await update_user(message.from_user.id, {"about": new_about})
    if ok:
        await message.answer("✅ Био успешно обновлено!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")]
        ]))
    else:
        await message.answer("❌ Ошибка при обновлении био.")

    await state.clear()


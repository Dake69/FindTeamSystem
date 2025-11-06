from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_ID
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bson import ObjectId



from keyboards.admin_keyboards import *


from FSM.all import *
from database.users import *
from database.games import *

from FSM.all import *

router = Router()

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    await callback.message.edit_text(
        "👑 <b>Админ-панель</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=admin_panel_kb
    )

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    await message.answer(
        "👑 <b>Админ-панель</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=admin_panel_kb
    )

@router.callback_query(F.data == "admin_games")
async def admin_games_menu(callback: CallbackQuery, state):
    await callback.message.edit_text(
        "🕹 <b>Управление играми</b>\n\n"
        "Здесь вы можете добавить новую игру, удалить существующую или посмотреть список всех игр.",
        parse_mode="HTML",
        reply_markup=admin_games_kb
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add_game")
async def admin_add_game_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Введите <b>название игры</b>:",
        parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb()
    )
    await state.set_state(AddGameFSM.waiting_for_name)
    await callback.answer()

@router.message(AddGameFSM.waiting_for_name)
async def admin_add_game_name(message: Message, state: FSMContext):
    await state.update_data(game_name=message.text)
    genres = await get_all_genres()
    if not genres:
        await message.answer("❗️ Нет ни одного жанра. Сначала добавьте жанр в разделе управления жанрами.")
        await state.clear()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=genre.get("name", "Без названия"), callback_data=f"select_genre_{str(genre['_id'])}")]
            for genre in genres
        ]
    )

    await message.answer(
        "🗂 <b>Выберите жанр для игры</b> с помощью кнопок ниже:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.set_state(AddGameFSM.waiting_for_genre)

@router.callback_query(F.data.startswith("select_genre_"))
async def admin_add_game_select_genre(callback: CallbackQuery, state: FSMContext):
    genre_id = callback.data.split("_", 2)[2]
    from database.games import get_genre_by_id
    genre = await get_genre_by_id(genre_id)
    if not genre:
        await callback.answer("❗️ Жанр не найден.", show_alert=True)
        return
    await state.update_data(genre=genre.get("name"))
    await callback.message.edit_text(
        "📝 Введите <b>описание игры</b> (или пропустите, отправив - ):",
        parse_mode="HTML"
    )
    await state.set_state(AddGameFSM.waiting_for_description)
    await callback.answer()


@router.message(AddGameFSM.waiting_for_genre)
async def admin_add_game_genre(message: Message, state: FSMContext):
    genre = message.text if message.text != "-" else None
    await state.update_data(genre=genre)
    await message.answer("📝 Введите <b>описание игры</b> (или пропустите, отправив - ):", parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb())
    await state.set_state(AddGameFSM.waiting_for_description)

@router.message(AddGameFSM.waiting_for_description)
async def admin_add_game_description(message: Message, state: FSMContext):
    description = message.text if message.text != "-" else None
    await state.update_data(description=description)
    await message.answer("🔢 Введите <b>количество рангов</b> для этой игры (число):", parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb())
    await state.set_state(AddGameFSM.waiting_for_ranks_count)

@router.message(AddGameFSM.waiting_for_ranks_count)
async def admin_add_game_ranks_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 0 or count > 50:
            raise ValueError
    except ValueError:
        await message.answer("❗️ Введите корректное положительное число (до 50).",
        reply_markup=get_cancel_to_games_kb())
        return
    await state.update_data(ranks_count=count, ranks=[], current_rank=1)
    if count == 0:
        data = await state.get_data()
        result = await add_game(
            game_name=data.get("game_name"),
            genre=data.get("genre"),
            description=data.get("description"),
            ranks=[]
        )
        if result.get("success"):
            await message.answer("✅ Игра успешно добавлена!")
        else:
            await message.answer(f"❌ Ошибка: {result.get('reason')}")
        await state.clear()
        return
    await message.answer(f"✏️ Введите название ранга №1 (от самого низкого к самому высокому):",
        reply_markup=get_cancel_to_games_kb())
    await state.set_state(AddGameFSM.waiting_for_rank_name)

@router.message(AddGameFSM.waiting_for_rank_name)
async def admin_add_game_rank_name(message: Message, state: FSMContext):
    data = await state.get_data()
    ranks = data.get("ranks", [])
    ranks.append(message.text)
    current_rank = data.get("current_rank", 1)
    ranks_count = data.get("ranks_count", 0)
    await state.update_data(ranks=ranks, current_rank=current_rank + 1)
    if len(ranks) < ranks_count:
        await message.answer(f"✏️ Введите название ранга №{len(ranks)+1} (по возрастанию):",
        reply_markup=get_cancel_to_games_kb())
        return
    data = await state.get_data()
    result = await add_game(
        game_name=data.get("game_name"),
        genre=data.get("genre"),
        description=data.get("description"),
        ranks=ranks
    )
    if result.get("success"):
        await message.answer("✅ Игра успешно добавлена!")
    else:
        await message.answer(f"❌ Ошибка: {result.get('reason')}")
    await state.clear()


@router.callback_query(F.data == "admin_show_games")
async def admin_show_games(callback: CallbackQuery, state: FSMContext):
    games = await get_all_games()
    if not games:
        await callback.message.edit_text("❗️ В базе нет ни одной игры.", parse_mode="HTML")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=game.get("game_name", "Без названия"), callback_data=f"game_{str(game['_id'])}")]
            for game in games
        ] + [
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_games")]
        ]
    )

    await callback.message.edit_text(
        "🎮 <b>Список всех игр:</b>\n\n"
        "Нажмите на игру для подробностей или управления.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("game_"))
async def admin_game_detail(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.split("_", 1)[1]
    game = await get_game_by_id(ObjectId(game_id))
    if not game:
        await callback.message.edit_text("❗️ Игра не найдена.", parse_mode="HTML")
        await callback.answer()
        return

    text = (
        f"🎮 <b>{game.get('game_name', 'Без названия')}</b>\n"
        f"🗂 <b>Жанр:</b> {game.get('genre', '—')}\n"
        f"📝 <b>Описание:</b> {game.get('description', '—')}"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_game_manage_kb(game_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_delete_game_"))
async def admin_delete_game(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.split("_", 3)[3]
    result = await delete_game(game_id)
    if result:
        await callback.message.edit_text("✅ Игра успешно удалена!", parse_mode="HTML")
    else:
        await callback.message.edit_text("❌ Ошибка при удалении игры.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("admin_edit_game_"))
async def admin_edit_game_start(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.split("_", 3)[3]
    game = await get_game_by_id(ObjectId(game_id))
    if not game:
        await callback.message.edit_text("❗️ Игра не найдена.", parse_mode="HTML")
        await callback.answer()
        return
    await state.update_data(game_id=game_id)
    await callback.message.edit_text(
        f"✏️ <b>Редактирование игры</b>\n\n"
        f"Текущее название: <b>{game.get('game_name', '—')}</b>\n"
        f"Введите новое название или отправьте <code>-</code> чтобы оставить без изменений:",
        parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb()
    )
    await state.set_state(EditGameFSM.waiting_for_name)
    await callback.answer()

@router.message(EditGameFSM.waiting_for_name)
async def admin_edit_game_name(message: Message, state: FSMContext):
    await state.update_data(new_name=message.text)
    await message.answer("🗂 Введите новый жанр или <code>-</code> чтобы оставить без изменений:", parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb())
    await state.set_state(EditGameFSM.waiting_for_genre)

@router.message(EditGameFSM.waiting_for_genre)
async def admin_edit_game_genre(message: Message, state: FSMContext):
    await state.update_data(new_genre=message.text)
    await message.answer("📝 Введите новое описание или <code>-</code> чтобы оставить без изменений:", parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb())
    await state.set_state(EditGameFSM.waiting_for_description)

@router.message(EditGameFSM.waiting_for_description)
async def admin_edit_game_description(message: Message, state: FSMContext):
    data = await state.get_data()
    game_id = data.get("game_id")
    update_data = {}

    if data.get("new_name") != "-":
        update_data["game_name"] = data.get("new_name")
    if data.get("new_genre") != "-":
        update_data["genre"] = data.get("new_genre")
    if message.text != "-":
        update_data["description"] = message.text

    if not update_data:
        await message.answer("❗️ Нет изменений для сохранения.")
        await state.clear()
        return

    from database.games import update_game
    result = await update_game(ObjectId(game_id), update_data)
    if result:
        await message.answer("✅ Игра успешно обновлена!",
        reply_markup=get_cancel_to_games_kb())
    else:
        await message.answer("❌ Ошибка при обновлении игры.")
    await state.clear()

@router.callback_query(F.data.startswith("admin_edit_ranks_"))
async def admin_edit_ranks_start(callback: CallbackQuery, state: FSMContext):
    game_id = callback.data.split("_", 3)[3]
    game = await get_game_by_id(ObjectId(game_id))
    if not game:
        await callback.message.edit_text("❗️ Игра не найдена.", parse_mode="HTML")
        await callback.answer()
        return
    await state.update_data(game_id=game_id)
    await callback.message.edit_text(
        f"🏆 <b>Редактирование рангов для игры:</b> <b>{game.get('game_name', '—')}</b>\n\n"
        f"Текущие ранги: {', '.join(game.get('ranks', [])) or '—'}\n\n"
        "🔢 Введите <b>новое количество рангов</b> для этой игры (число):",
        parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb()
    )
    await state.set_state(EditRanksFSM.waiting_for_ranks_count)
    await callback.answer()

@router.message(EditRanksFSM.waiting_for_ranks_count)
async def admin_edit_ranks_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 0 or count > 50:
            raise ValueError
    except ValueError:
        await message.answer("❗️ Введите корректное положительное число (до 50).",
        reply_markup=get_cancel_to_games_kb())
        return
    await state.update_data(ranks_count=count, ranks=[], current_rank=1)
    if count == 0:
        data = await state.get_data()
        from database.games import update_game
        result = await update_game(ObjectId(data.get("game_id")), {"ranks": []})
        if result:
            await message.answer("✅ Ранги успешно обновлены (удалены)!",
            reply_markup=get_cancel_to_games_kb())
        else:
            await message.answer("❌ Ошибка при обновлении рангов.")
        await state.clear()
        return
    await message.answer(f"✏️ Введите название ранга №1 (от самого низкого к самому высокому):")
    await state.set_state(EditRanksFSM.waiting_for_rank_name)

@router.message(EditRanksFSM.waiting_for_rank_name)
async def admin_edit_ranks_name(message: Message, state: FSMContext):
    data = await state.get_data()
    ranks = data.get("ranks", [])
    ranks.append(message.text)
    current_rank = data.get("current_rank", 1)
    ranks_count = data.get("ranks_count", 0)
    await state.update_data(ranks=ranks, current_rank=current_rank + 1)
    if len(ranks) < ranks_count:
        await message.answer(f"✏️ Введите название ранга №{len(ranks)+1} (по возрастанию):",
        reply_markup=get_cancel_to_games_kb())
        return
    data = await state.get_data()
    from database.games import update_game
    result = await update_game(ObjectId(data.get("game_id")), {"ranks": ranks})
    if result:
        await message.answer("✅ Ранги успешно обновлены!",
        reply_markup=get_cancel_to_games_kb())
    else:
        await message.answer("❌ Ошибка при обновлении рангов.")
    await state.clear()

@router.callback_query(F.data == "admin_add_genre")
async def admin_add_genre_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Введите <b>название жанра</b>:",
        parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb()
    )
    await state.set_state(AddGenreFSM.waiting_for_name)
    await callback.answer()

@router.message(AddGenreFSM.waiting_for_name)
async def admin_add_genre_name(message: Message, state: FSMContext):
    await state.update_data(genre_name=message.text)
    await message.answer("📝 Введите <b>описание жанра</b> (или пропустите, отправив - ):", parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb())
    await state.set_state(AddGenreFSM.waiting_for_description)

@router.message(AddGenreFSM.waiting_for_description)
async def admin_add_genre_description(message: Message, state: FSMContext):
    description = message.text if message.text != "-" else ""
    data = await state.get_data()
    from database.games import add_genre
    result = await add_genre(data.get("genre_name"), description)
    if result.get("success"):
        await message.answer("✅ Жанр успешно добавлен!")
    else:
        await message.answer(f"❌ Ошибка: {result.get('reason')}")
    await state.clear()

@router.callback_query(F.data == "admin_show_genres")
async def admin_show_genres(callback: CallbackQuery, state: FSMContext):
    from database.games import get_all_genres
    genres = await get_all_genres()
    if not genres:
        await callback.message.edit_text("❗️ В базе нет ни одного жанра.", parse_mode="HTML")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=genre.get("name", "Без названия"), callback_data=f"genre_{str(genre['_id'])}")]
            for genre in genres
        ] + [
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_games")]
        ]
    )

    await callback.message.edit_text(
        "🎭 <b>Список всех жанров:</b>\n\n"
        "Нажмите на жанр для подробностей или управления.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("genre_"))
async def admin_genre_detail(callback: CallbackQuery, state: FSMContext):
    genre_id = callback.data.split("_", 1)[1]
    from database.games import get_genre_by_id
    genre = await get_genre_by_id(genre_id)
    if not genre:
        await callback.message.edit_text("❗️ Жанр не найден.", parse_mode="HTML")
        await callback.answer()
        return

    text = (
        f"🎭 <b>{genre.get('name', 'Без названия')}</b>\n"
        f"📝 <b>Описание:</b> {genre.get('description', '—')}"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_genre_manage_kb(genre_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_edit_genre_"))
async def admin_edit_genre_start(callback: CallbackQuery, state: FSMContext):
    genre_id = callback.data.split("_", 3)[3]
    from database.games import get_genre_by_id
    genre = await get_genre_by_id(genre_id)
    if not genre:
        await callback.message.edit_text("❗️ Жанр не найден.", parse_mode="HTML")
        await callback.answer()
        return
    await state.update_data(genre_id=genre_id)
    await callback.message.edit_text(
        f"✏️ <b>Редактирование жанра</b>\n\n"
        f"Текущее название: <b>{genre.get('name', '—')}</b>\n"
        f"Введите новое название или отправьте <code>-</code> чтобы оставить без изменений:",
        parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb()
    )
    await state.set_state(EditGenreFSM.waiting_for_name)
    await callback.answer()

@router.message(EditGenreFSM.waiting_for_name)
async def admin_edit_genre_name(message: Message, state: FSMContext):
    await state.update_data(new_name=message.text)
    await message.answer("📝 Введите новое описание или <code>-</code> чтобы оставить без изменений:", parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb())
    await state.set_state(EditGenreFSM.waiting_for_description)

@router.message(EditGenreFSM.waiting_for_description)
async def admin_edit_genre_description(message: Message, state: FSMContext):
    data = await state.get_data()
    genre_id = data.get("genre_id")
    update_data = {}
    if data.get("new_name") != "-":
        update_data["name"] = data.get("new_name")
    if message.text != "-":
        update_data["description"] = message.text

    if not update_data:
        await message.answer("❗️ Нет изменений для сохранения.")
        await state.clear()
        return

    from database.games import update_genre
    result = await update_genre(genre_id, update_data)
    if result:
        await message.answer("✅ Жанр успешно обновлён!",
        reply_markup=get_cancel_to_games_kb())
    else:
        await message.answer("❌ Ошибка при обновлении жанра.")
    await state.clear()

@router.callback_query(F.data.startswith("admin_delete_genre_"))
async def admin_delete_genre(callback: CallbackQuery, state: FSMContext):
    genre_id = callback.data.split("_", 3)[3]
    from database.games import delete_genre
    result = await delete_genre(genre_id)
    if result:
        await callback.message.edit_text("✅ Жанр успешно удалён!", parse_mode="HTML",
        reply_markup=get_cancel_to_games_kb())
    else:
        await callback.message.edit_text("❌ Ошибка при удалении жанра.", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_languages")
async def admin_languages_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🌐 <b>Управление языками</b>\n\n"
        "Здесь вы можете добавить новый язык, удалить существующий или посмотреть список всех языков.",
        parse_mode="HTML",
        reply_markup=admin_languages_kb
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add_language")
async def admin_add_language_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Введите <b>название языка</b>:",
        parse_mode="HTML",
        reply_markup=get_cancel_to_languages_kb()
    )
    await state.set_state(AddLanguageFSM.waiting_for_name)
    await callback.answer()

@router.message(AddLanguageFSM.waiting_for_name)
async def admin_add_language_name(message: Message, state: FSMContext):
    await state.update_data(language_name=message.text)
    await message.answer("🌐 Введите <b>код языка</b> (например, ru, en) или отправьте <code>-</code> чтобы пропустить:",
        parse_mode="HTML", reply_markup=get_cancel_to_languages_kb())
    await state.set_state(AddLanguageFSM.waiting_for_code)

@router.message(AddLanguageFSM.waiting_for_code)
async def admin_add_language_code(message: Message, state: FSMContext):
    code = message.text if message.text != "-" else None
    data = await state.get_data()
    from database.language import add_language
    result = await add_language(data.get("language_name"), code)
    if result:
        await message.answer("✅ Язык успешно добавлен!", reply_markup=get_cancel_to_languages_kb())
    else:
        await message.answer("❌ Ошибка при добавлении языка.")
    await state.clear()

@router.callback_query(F.data == "admin_show_languages")
async def admin_show_languages(callback: CallbackQuery, state: FSMContext):
    from database.language import get_all_languages
    langs = await get_all_languages()
    if not langs:
        await callback.message.edit_text("❗️ В базе нет ни одного языка.", parse_mode="HTML")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lang.get("name", "Без названия"), callback_data=f"language_{str(lang['_id'])}")]
            for lang in langs
        ] + [
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_languages")]
        ]
    )

    await callback.message.edit_text(
        "🌐 <b>Список всех языков:</b>\n\n"
        "Нажмите на язык для подробностей или управления.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("language_"))
async def admin_language_detail(callback: CallbackQuery, state: FSMContext):
    language_id = callback.data.split("_", 1)[1]
    from database.language import get_language_by_id
    lang = await get_language_by_id(language_id)
    if not lang:
        await callback.message.edit_text("❗️ Язык не найден.", parse_mode="HTML")
        await callback.answer()
        return

    text = (
        f"🌐 <b>{lang.get('name', 'Без названия')}</b>\n"
        f"🔤 <b>Код:</b> {lang.get('code', '—')}"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_language_manage_kb(language_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_edit_language_"))
async def admin_edit_language_start(callback: CallbackQuery, state: FSMContext):
    language_id = callback.data.split("_", 3)[3]
    from database.language import get_language_by_id
    lang = await get_language_by_id(language_id)
    if not lang:
        await callback.message.edit_text("❗️ Язык не найден.", parse_mode="HTML")
        await callback.answer()
        return
    await state.update_data(language_id=language_id)
    await callback.message.edit_text(
        f"✏️ <b>Редактирование языка</b>\n\n"
        f"Текущее название: <b>{lang.get('name', '—')}</b>\n"
        f"Введите новое название или отправьте <code>-</code> чтобы оставить без изменений:",
        parse_mode="HTML",
        reply_markup=get_cancel_to_languages_kb()
    )
    await state.set_state(EditLanguageFSM.waiting_for_name)
    await callback.answer()

@router.message(EditLanguageFSM.waiting_for_name)
async def admin_edit_language_name(message: Message, state: FSMContext):
    await state.update_data(new_name=message.text)
    await message.answer("🔤 Введите новый код языка или <code>-</code> чтобы оставить без изменений:", parse_mode="HTML",
        reply_markup=get_cancel_to_languages_kb())
    await state.set_state(EditLanguageFSM.waiting_for_code)

@router.message(EditLanguageFSM.waiting_for_code)
async def admin_edit_language_code(message: Message, state: FSMContext):
    data = await state.get_data()
    language_id = data.get("language_id")
    update_data = {}
    if data.get("new_name") != "-":
        update_data["name"] = data.get("new_name")
    if message.text != "-":
        update_data["code"] = message.text

    if not update_data:
        await message.answer("❗️ Нет изменений для сохранения.")
        await state.clear()
        return

    from database.language import update_language
    result = await update_language(language_id, update_data)
    if result:
        await message.answer("✅ Язык успешно обновлён!",
        reply_markup=get_cancel_to_languages_kb())
    else:
        await message.answer("❌ Ошибка при обновлении языка.")
    await state.clear()

@router.callback_query(F.data.startswith("admin_delete_language_"))
async def admin_delete_language(callback: CallbackQuery, state: FSMContext):
    language_id = callback.data.split("_", 3)[3]
    from database.language import delete_language
    result = await delete_language(language_id)
    if result:
        await callback.message.edit_text("✅ Язык успешно удалён!", parse_mode="HTML",
        reply_markup=get_cancel_to_languages_kb())
    else:
        await callback.message.edit_text("❌ Ошибка при удалении языка.", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery, state: FSMContext):
    users = await get_all_active_users()
    if not users:
        await callback.message.edit_text("❗️ Нет активных пользователей.", parse_mode="HTML",
                                         reply_markup=admin_panel_kb)
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{u.get('nickname') or u.get('full_name')} ({u.get('user_id')})",
                                  callback_data=f"admin_user_{u.get('user_id')}")]
            for u in users
        ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]]
    )

    await callback.message.edit_text(
        "👥 <b>Активные пользователи</b>:\n\nНажмите на пользователя для управления.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_"))
async def admin_user_detail(callback: CallbackQuery, state: FSMContext):
    user_id = callback.data.split("_", 2)[2]
    try:
        uid = int(user_id)
    except Exception:
        uid = user_id
    user = await get_user_by_id(uid)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    games = user.get('games', {})
    games_text = ', '.join(games.keys()) if games else '—'
    text = (
        f"👤 <b>{user.get('full_name', '—')}</b>\n"
        f"🆔 <b>ID:</b> {user.get('user_id')}\n"
        f"🔹 <b>Ник:</b> {user.get('nickname', '—')}\n"
        f"🔹 <b>Username:</b> @{user.get('username') if user.get('username') else '—'}\n"
        f"🎮 <b>Игры:</b> {games_text}\n"
        f"🌐 <b>Языки:</b> {', '.join(user.get('languages', [])) or '—'}\n"
        f"⚪️ <b>Активен:</b> {user.get('is_active', True)}\n"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_user_manage_kb(user.get('user_id'), user.get('is_active', True), user.get('is_banned', False))
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_ban_"))
async def admin_ban_user(callback: CallbackQuery):
    user_id = callback.data.split("_", 2)[2]
    try:
        uid = int(user_id)
    except Exception:
        uid = user_id
    await update_user(uid, {"is_active": False, "is_banned": True})
    try:
        await callback.bot.send_message(uid, "⛔️ Вы были забанены администратором.")
    except Exception:
        pass
    await callback.message.edit_text("✅ Пользователь успешно забанен.", reply_markup=admin_panel_kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_unban_"))
async def admin_unban_user(callback: CallbackQuery):
    user_id = callback.data.split("_", 2)[2]
    try:
        uid = int(user_id)
    except Exception:
        uid = user_id
    await update_user(uid, {"is_active": True, "is_banned": False})
    try:
        await callback.bot.send_message(uid, "✅ Вам снят бан. Вы снова в системе.")
    except Exception:
        pass
    await callback.message.edit_text("✅ Пользователь разбанен.", reply_markup=admin_panel_kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_active_"))
async def admin_toggle_active(callback: CallbackQuery):
    user_id = callback.data.split("_", 3)[3] if callback.data.count("_") >= 3 else callback.data.split("_",2)[2]
    try:
        uid = int(user_id)
    except Exception:
        uid = user_id
    user = await get_user_by_id(uid)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return
    new_active = not user.get('is_active', True)
    await update_user(uid, {"is_active": new_active})
    await callback.message.edit_text(f"✅ Статус активности изменён: {new_active}", reply_markup=admin_panel_kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_warn_"))
async def admin_warn_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.data.split("_", 2)[2]
    await state.update_data(target_user=user_id)
    await callback.message.edit_text("✉️ Отправьте текст предупреждения для пользователя:")
    await state.set_state(AdminWarnFSM.waiting_for_text)
    await callback.answer()


@router.message(AdminWarnFSM.waiting_for_text)
async def admin_send_warning(message: Message, state: FSMContext):
    data = await state.get_data()
    target = data.get('target_user')
    try:
        uid = int(target)
    except Exception:
        uid = target
    text = message.text
    try:
        await message.bot.send_message(uid, f"⚠️ Сообщение от администрации:\n\n{text}")
        await message.answer("✅ Сообщение отправлено пользователю.")
    except Exception:
        await message.answer("❌ Не удалось отправить сообщение (пользователь заблокировал бота или ошибка).")
    await state.clear()
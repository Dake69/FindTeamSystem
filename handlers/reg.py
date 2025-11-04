from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from FSM.all import RegistrationInline
import logging


from keyboards.reg import *
from database.users import *
from database.games import get_game_by_name
from database.language import get_all_languages
from database.filtrs import *


router = Router()

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    # Показываем ID пользователя для настройки админки
    print(f"[DEBUG] User {message.from_user.username} ID: {message.from_user.id}")
    
    user = await get_user_by_id(message.from_user.id)
    if user:
        await message.answer(
            "👋 <b>Добро пожаловать обратно!</b>\n\n"
            "🎮 Вы уже зарегистрированы в FindTeamBot!\n"
            "Здесь вы сможете найти друзей для совместных каток, познакомиться с новыми игроками и собрать свою команду мечты! 🏆\n\n"
            "🏠 <b>Вы перенаправлены в главное меню. Используйте кнопку ниже для навигации по боту.</b>",
            parse_mode="HTML",
            reply_markup=main_menu_inline_kb
        )
        return
    await message.answer(
        "👋 <b>Добро пожаловать в FindTeamBot!</b>\n\n"
        "📝 Для поиска тиммейтов заполните анкету.\n"
        "Введите ваше <b>имя</b>:",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.full_name)

@router.message(RegistrationInline.full_name, F.text)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("📝 Введите ваш <b>никнейм</b>:", parse_mode="HTML")
    await state.set_state(RegistrationInline.nickname)

@router.message(RegistrationInline.nickname, F.text)
async def get_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer("🎂 Введите ваш <b>возраст</b>:", parse_mode="HTML")
    await state.set_state(RegistrationInline.age)

@router.message(RegistrationInline.age, F.text)
async def get_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age < 10 or age > 99:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректный возраст (10-99):")
        return
    await state.update_data(age=age)
    await message.answer("🧑 Выберите ваш <b>пол</b>:", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мужской", callback_data="gender_male"),
             InlineKeyboardButton(text="Женский", callback_data="gender_female")]
        ]
    ), parse_mode="HTML")
    await state.set_state(RegistrationInline.gender)

@router.callback_query(RegistrationInline.gender, F.data.startswith("gender_"))
async def get_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await callback.message.edit_text("📝 Напишите <b>коротко о себе</b> (био):", parse_mode="HTML")
    await state.set_state(RegistrationInline.about)
    await callback.answer()

@router.message(RegistrationInline.about, F.text)
async def get_about(message: Message, state: FSMContext):
    await state.update_data(about=message.text)
    skip_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_photo")]
        ]
    )
    await message.answer(
        "📸 Отправьте ваше <b>фото</b> (аватарку):\n\nИли нажмите 'Пропустить', чтобы продолжить без фото.",
        reply_markup=skip_kb,
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.photo)

@router.message(RegistrationInline.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo_id=photo.file_id)
    await message.answer(
        "📱 Пожалуйста, отправьте ваш <b>номер телефона</b>:",
        reply_markup=contact_kb,
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.phone)

@router.callback_query(RegistrationInline.photo, F.data == "skip_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo_id=None)
    await callback.message.edit_text(
        "📱 Пожалуйста, отправьте ваш <b>номер телефона</b>:",
        parse_mode="HTML"
    )
    await callback.message.answer(
        "Нажмите кнопку ниже:",
        reply_markup=contact_kb
    )
    await state.set_state(RegistrationInline.phone)
    await callback.answer()

@router.message(RegistrationInline.phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer(
        "🎮 Выберите одну или несколько игр (нажимайте по очереди):",
        reply_markup=await get_games_keyboard([]),
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.game)

@router.callback_query(RegistrationInline.game, F.data)
async def choose_games(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_games = data.get("games", [])
    logging.info(f"[choose_games] selected_games: {selected_games}, callback.data: {callback.data}")
    if callback.data.startswith("game_"):
        game = callback.data[5:]
        if game in selected_games:
            selected_games.remove(game)
        else:
            selected_games.append(game)
        await state.update_data(games=selected_games)
        logging.info(f"[choose_games] updated selected_games: {selected_games}")
        await callback.message.edit_text(
            "🎮 Выберите одну или несколько игр (нажимайте по очереди):",
            reply_markup=await get_games_keyboard(selected_games),
            parse_mode="HTML"
        )
    elif callback.data == "games_done":
        if not selected_games:
            await callback.answer("Выберите хотя бы одну игру!", show_alert=True)
            return
        await state.update_data(games_with_ranks={})
        await state.set_state(RegistrationInline.rank)
        await ask_game_rank(callback, state, 0)
    else:
        await callback.answer()

async def ask_game_rank(callback, state, game_idx):
    data = await state.get_data()
    games = data.get("games", [])
    logging.info(f"[ask_game_rank] game_idx: {game_idx}, games: {games}")
    if game_idx >= len(games):
        await callback.message.edit_text(
            "🌐 Выберите ваш <b>язык</b> общения:",
            reply_markup=await get_languages_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(RegistrationInline.language)
        return

    game_name = games[game_idx]
    game = await get_game_by_name(game_name)
    ranks = game.get("ranks", [])
    logging.info(f"[ask_game_rank] game_name: {game_name}, ranks: {ranks}")

    current_text = f"🏆 Выберите ваш <b>ранг</b> в игре <b>{game_name}</b>:"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=rank, callback_data=f"rank_{game_idx}_{rank}")]
            for rank in ranks
        ]
    )

    if callback.message.text == current_text and callback.message.reply_markup == keyboard:
        await callback.answer("Вы уже видите этот выбор.")
        return

    await callback.message.edit_text(
        current_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(RegistrationInline.rank, F.data.startswith("rank_"))
async def select_game_rank(callback: CallbackQuery, state: FSMContext):
    logging.info(f"[select_game_rank] callback.data: {callback.data}")
    _, game_idx, *rank_parts = callback.data.split("_")
    game_idx = int(game_idx)
    rank = "_".join(rank_parts)
    data = await state.get_data()
    games = data.get("games", [])
    games_with_ranks = data.get("games_with_ranks", {})
    logging.info(f"[select_game_rank] game_idx: {game_idx}, rank: {rank}, games: {games}, games_with_ranks: {games_with_ranks}")

    if game_idx >= len(games):
        await callback.answer("Ошибка выбора игры.", show_alert=True)
        logging.warning(f"[select_game_rank] game_idx {game_idx} >= len(games) {len(games)}")
        return

    game_name = games[game_idx]
    if games_with_ranks.get(game_name) == rank:
        await callback.answer("Этот ранг уже выбран.")
        return

    games_with_ranks[game_name] = rank
    await state.update_data(games_with_ranks=games_with_ranks)
    logging.info(f"[select_game_rank] updated games_with_ranks: {games_with_ranks}")

    if game_idx + 1 < len(games):
        await ask_game_rank(callback, state, game_idx + 1)
    else:
        await state.set_state(RegistrationInline.language)
        await callback.message.edit_text(
            "🌐 Выберите ваш <b>язык</b> общения:",
            reply_markup=await get_languages_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()

async def get_languages_keyboard():
    langs = await get_all_languages()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lang["name"], callback_data=f"lang_{lang['_id']}")]
            for lang in langs
        ]
    )

@router.callback_query(RegistrationInline.language, F.data.startswith("lang_"))
async def select_language(callback: CallbackQuery, state: FSMContext):
    language_id = callback.data.split("_", 1)[1]
    await state.update_data(language=language_id)
    data = await state.get_data()
    result = await add_user(
        user_id=callback.from_user.id,
        full_name=data.get('full_name'),
        nickname=data.get('nickname'),
        age=data.get('age'),
        gender=data.get('gender'),
        about=data.get('about'),
        photo_id=data.get('photo_id'),
        phone=data.get('phone'),
        games_with_ranks=data.get('games_with_ranks'),
        username=callback.from_user.username,
        language=language_id
    )
    if result.get("success"):
        games_str = "\n".join(
            [f"🎮 <b>{g}</b>: <i>{r}</i>" for g, r in data.get('games_with_ranks', {}).items()]
        )
        await callback.message.edit_text(
            "<b>✅ Регистрация завершена!</b>\n\n"
            f"👤 <b>Имя:</b> {data.get('full_name')}\n"
            f"🏷️ <b>Никнейм:</b> {data.get('nickname')}\n"
            f"🎂 <b>Возраст:</b> {data.get('age')}\n"
            f"🧑 <b>Пол:</b> {'Мужской' if data.get('gender') == 'male' else 'Женский'}\n"
            f"📱 <b>Телефон:</b> {data.get('phone')}\n"
            f"{games_str}\n"
            f"📝 <b>О себе:</b> {data.get('about')}",
            parse_mode="HTML",
            reply_markup=main_menu_inline_kb
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Ошибка:</b> {result.get('reason')}",
            parse_mode="HTML"
        )
    await state.clear()

@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext):
    temp = await get_filter_by_user(callback.from_user.id)
    if temp:
        pass
    else:
        await add_filter(
            user_id=callback.from_user.id,
        )
    text = (
        "🏠 <b>Главное меню</b>\n\n"
        "📰 <b>Лента</b> — смотрите анкеты других игроков и ставьте лайки\n\n"
        "🎯 <b>Мои матчи</b> — просматривайте свои совпадения\n\n"
        "👤 <b>Профиль</b> — управляйте своей анкетой\n\n"
        "⚙️ <b>Настройки</b> — настройте фильтры поиска\n\n"
        "Выберите нужный раздел с помощью кнопок ниже 👇"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_kb)
    await callback.answer()
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from FSM.all import RegistrationInline

from keyboards.reg import *

from database.users import *

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
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
    await callback.message.edit_text("🏙 Введите ваш <b>город</b>:", parse_mode="HTML")
    await state.set_state(RegistrationInline.city)
    await callback.answer()

@router.message(RegistrationInline.city, F.text)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("📝 Напишите <b>коротко о себе</b> (био):", parse_mode="HTML")
    await state.set_state(RegistrationInline.about)

@router.message(RegistrationInline.about, F.text)
async def get_about(message: Message, state: FSMContext):
    await state.update_data(about=message.text)
    await message.answer(
        "📱 Пожалуйста, отправьте ваш <b>номер телефона</b>:",
        reply_markup=contact_kb,
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.phone)

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
    if callback.data.startswith("game_"):
        game = callback.data[5:]
        if game in selected_games:
            selected_games.remove(game)
        else:
            selected_games.append(game)
        await state.update_data(games=selected_games)
        await callback.message.edit_text(
            "🎮 Выберите одну или несколько игр (нажимайте по очереди):",
            reply_markup=await get_games_keyboard(selected_games),
            parse_mode="HTML"
        )
    elif callback.data == "games_done":
        if not selected_games:
            await callback.answer("Выберите хотя бы одну игру!", show_alert=True)
            return
        data = await state.get_data()
        result = await add_user(
            user_id=callback.from_user.id,
            full_name=data.get('full_name'),
            nickname=data.get('nickname'),
            age=data.get('age'),
            gender=data.get('gender'),
            city=data.get('city'),
            about=data.get('about'),
            phone=data.get('phone'),
            games=selected_games,
            username=callback.from_user.username
        )
        if result.get("success"):
            await callback.message.edit_text(
                "<b>✅ Регистрация завершена!</b>\n\n"
                f"👤 <b>Имя:</b> {data.get('full_name')}\n"
                f"🏷️ <b>Никнейм:</b> {data.get('nickname')}\n"
                f"🎂 <b>Возраст:</b> {data.get('age')}\n"
                f"🧑 <b>Пол:</b> {'Мужской' if data.get('gender') == 'male' else 'Женский'}\n"
                f"🏙 <b>Город:</b> {data.get('city')}\n"
                f"📱 <b>Телефон:</b> {data.get('phone')}\n"
                f"🎮 <b>Игры:</b> {', '.join(selected_games)}\n"
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
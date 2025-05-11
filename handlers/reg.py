from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from FSM.all import RegistrationInline

from keyboards.reg import *

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Пожалуйста, введите ваше <b>ФИО</b>:",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.full_name)

@router.message(RegistrationInline.full_name, F.text)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer(
        "📝 Введите ваш <b>никнейм</b>:",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.nickname)

@router.message(RegistrationInline.nickname, F.text)
async def get_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer(
        "📱 Пожалуйста, отправьте ваш <b>номер телефона</b>:",
        reply_markup=contact_kb,
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.phone)

@router.message(RegistrationInline.phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    selected_games = []
    await state.update_data(phone=message.contact.phone_number)
    await message.answer(
        "🎮 Выберите одну или несколько игр (нажимайте по очереди):",
        reply_markup=get_games_keyboard(selected_games),
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
            reply_markup=get_games_keyboard(selected_games),
            parse_mode="HTML"
        )
    elif callback.data == "games_done":
        if not selected_games:
            await callback.answer("Выберите хотя бы одну игру!", show_alert=True)
            return
        data = await state.get_data()
        await callback.message.edit_text(
            "<b>✅ Регистрация завершена!</b>\n\n"
            f"👤 <b>ФИО:</b> {data.get('full_name')}\n"
            f"🏷️ <b>Никнейм:</b> {data.get('nickname')}\n"
            f"📱 <b>Телефон:</b> {data.get('phone')}\n"
            f"🎮 <b>Игры:</b> {', '.join(selected_games)}",
            parse_mode="HTML"
        )
        await state.clear()
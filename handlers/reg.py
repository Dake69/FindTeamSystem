from aiogram import Router
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

@router.message(RegistrationInline.full_name)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer(
        "📝 Введите ваш <b>никнейм</b>:",
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.nickname)

@router.message(RegistrationInline.nickname)
async def get_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer(
        "📱 Пожалуйста, отправьте ваш <b>номер телефона</b>:",
        reply_markup=contact_kb,
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.phone)

@router.message(RegistrationInline.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer(
        "🎮 Выберите вашу <b>игру</b>:",
        reply_markup=game_kb,
        parse_mode="HTML"
    )
    await state.set_state(RegistrationInline.game)

@router.callback_query(RegistrationInline.game)
async def choose_game(callback: CallbackQuery, state: FSMContext):
    await state.update_data(game=callback.data)
    data = await state.get_data()
    await callback.message.edit_text(
        "<b>✅ Регистрация завершена!</b>\n\n"
        f"👤 <b>ФИО:</b> {data.get('full_name')}\n"
        f"🏷️ <b>Никнейм:</b> {data.get('nickname')}\n"
        f"📱 <b>Телефон:</b> {data.get('phone')}\n"
        f"🎮 <b>Игра:</b> {data.get('game')}",
        parse_mode="HTML"
    )
    await state.clear()
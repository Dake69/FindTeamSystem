from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from FSM.all import RegistrationInline, EditProfileFSM

from database.users import *

router = Router()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_id(callback.from_user.id)
    
    if not user:
        await callback.message.edit_text(
            "❌ Профиль не найден. Пожалуйста, зарегистрируйтесь с помощью /start",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    games_str = "\n".join([f"  🎮 <b>{game}</b>: <i>{rank}</i>" for game, rank in user.get("games", {}).items()])
    gender_text = "Мужской" if user.get("gender") == "male" else "Женский"
    
    from database.language import get_language_by_id
    languages = user.get("languages", [])
    languages_names = []
    for lang_id in languages:
        lang = await get_language_by_id(lang_id)
        if lang:
            languages_names.append(lang.get("name"))
    languages_str = ", ".join(languages_names) if languages_names else "Не указаны"
    
    profile_text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"📛 <b>Имя:</b> {user.get('full_name')}\n"
        f"🏷️ <b>Никнейм:</b> {user.get('nickname')}\n"
        f"🎂 <b>Возраст:</b> {user.get('age')}\n"
        f"🧑 <b>Пол:</b> {gender_text}\n"
        f"🌐 <b>Языки:</b> {languages_str}\n"
        f"📝 <b>О себе:</b>\n{user.get('about')}\n\n"
        f"<b>🎮 Ваши игры:</b>\n{games_str if games_str else '  Не указаны'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data="edit_profile")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    photo_id = user.get("photo_id")
    if photo_id:
        await callback.message.delete()
        await callback.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=photo_id,
            caption=profile_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(profile_text, parse_mode="HTML", reply_markup=keyboard)
    
    await callback.answer()


@router.callback_query(F.data == "edit_profile")
async def edit_profile_menu(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить имя", callback_data="edit_fullname")],
        [InlineKeyboardButton(text="🏷️ Изменить никнейм", callback_data="edit_nickname")],
        [InlineKeyboardButton(text="📄 Изменить био", callback_data="edit_about")],
        [InlineKeyboardButton(text="📸 Изменить фото", callback_data="edit_photo")],
        [InlineKeyboardButton(text="🎮 Изменить игры", callback_data="edit_games")],
        [InlineKeyboardButton(text="⬅️ Назад к профилю", callback_data="profile")]
    ])
    
    try:
        await callback.message.edit_text(
            "✏️ <b>Редактирование профиля</b>\n\n"
            "Выберите, что хотите изменить:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except:
        await callback.message.answer(
            "✏️ <b>Редактирование профиля</b>\n\n"
            "Выберите, что хотите изменить:",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    await callback.answer()

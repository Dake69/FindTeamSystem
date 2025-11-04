from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from FSM.all import EditProfileFSM

from database.users import users_collection

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

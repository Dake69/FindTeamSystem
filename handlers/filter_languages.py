from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from FSM.all import FilterFSM

from database.filtrs import get_filter_by_user, update_filter
from database.language import get_all_languages

router = Router()


@router.callback_query(F.data == "edit_filter_languages")
async def edit_filter_languages_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_filter = await get_filter_by_user(user_id)
    selected_languages = user_filter.get("languages", []) if user_filter else []
    
    await state.update_data(filter_languages=selected_languages)
    await state.set_state(FilterFSM.languages)
    
    langs = await get_all_languages()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'✅ ' if str(lang['_id']) in selected_languages else ''}{lang['name']}",
                callback_data=f"toggle_filter_lang_{lang['_id']}"
            )]
            for lang in langs
        ] + [[InlineKeyboardButton(text="🎯 Готово", callback_data="filter_languages_done")]]
    )
    
    await callback.message.edit_text(
        "🌐 <b>Выберите языки для фильтра</b> (можно несколько):\n\n"
        "Вы будете видеть пользователей, у которых есть хотя бы один из выбранных языков.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(FilterFSM.languages, F.data.startswith("toggle_filter_lang_"))
async def toggle_filter_language(callback: CallbackQuery, state: FSMContext):
    lang_id = callback.data.replace("toggle_filter_lang_", "")
    data = await state.get_data()
    selected_languages = data.get("filter_languages", [])
    
    if lang_id in selected_languages:
        selected_languages.remove(lang_id)
    else:
        selected_languages.append(lang_id)
    
    await state.update_data(filter_languages=selected_languages)
    
    langs = await get_all_languages()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'✅ ' if str(lang['_id']) in selected_languages else ''}{lang['name']}",
                callback_data=f"toggle_filter_lang_{lang['_id']}"
            )]
            for lang in langs
        ] + [[InlineKeyboardButton(text="🎯 Готово", callback_data="filter_languages_done")]]
    )
    
    await callback.message.edit_text(
        "🌐 <b>Выберите языки для фильтра</b> (можно несколько):\n\n"
        "Вы будете видеть пользователей, у которых есть хотя бы один из выбранных языков.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(FilterFSM.languages, F.data == "filter_languages_done")
async def save_filter_languages(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_languages = data.get("filter_languages", [])
    
    await update_filter(callback.from_user.id, {"languages": selected_languages})
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Фильтр по языкам обновлён.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_filters")]
            ]
        )
    )
    await callback.answer()

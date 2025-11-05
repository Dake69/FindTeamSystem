from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database.users import get_user_by_id, get_all_active_users
from database.matches import create_match, get_user_matches
from database.filtrs import get_filter_by_user

router = Router()


async def format_user_card(user):
    games_str = " | ".join([f"{game}" for game in user.get("games", {}).keys()])
    gender_emoji = "👨" if user.get("gender") == "male" else "👩"
    
    from database.language import get_language_by_id
    languages = user.get("languages", [])
    languages_names = []
    for lang_id in languages:
        lang = await get_language_by_id(lang_id)
        if lang:
            languages_names.append(lang.get("name"))
    languages_str = ", ".join(languages_names) if languages_names else "Не указаны"
    
    text = (
        f"{gender_emoji} <b>{user.get('nickname')}</b>, {user.get('age')}\n\n"
        f"🎮 <b>Игры:</b> {games_str}\n"
        f"🌐 <b>Языки:</b> {languages_str}\n\n"
        f"📝 <b>О себе:</b>\n{user.get('about')}\n\n"
    )
    
    games_detail = []
    for game, rank in user.get("games", {}).items():
        games_detail.append(f"  • {game}: <i>{rank}</i>")
    
    if games_detail:
        text += "🏆 <b>Ранги:</b>\n" + "\n".join(games_detail)
    
    return text


async def get_next_candidate(current_user_id, user_filter):
    all_users = await get_all_active_users(limit=100)
    user_matches = await get_user_matches(current_user_id)
    
    viewed_ids = {current_user_id}
    for match in user_matches:
        # Исключаем тех, кому текущий пользователь УЖЕ поставил лайк или пропустил
        if match.get("user_id_1") == current_user_id:
            # Это наши исходящие действия
            if match.get("status") in ["pending", "skipped", "accepted"]:
                viewed_ids.add(match.get("user_id_2"))
        # НЕ исключаем, если это входящий лайк (user_id_2 == current_user_id)
        # Это позволит увидеть того, кто нам поставил лайк
    
    for candidate in all_users:
        if candidate.get("user_id") in viewed_ids:
            continue
        
        if user_filter:
            filter_games = user_filter.get("games", [])
            if filter_games:
                candidate_games = set(candidate.get("games", {}).keys())
                if not any(g in candidate_games for g in filter_games):
                    continue
            
            filter_gender = user_filter.get("gender", "any")
            if filter_gender != "any" and candidate.get("gender") != filter_gender:
                continue
            
            age_min = user_filter.get("age_min")
            age_max = user_filter.get("age_max")
            candidate_age = candidate.get("age")
            if age_min and candidate_age < age_min:
                continue
            if age_max and candidate_age > age_max:
                continue
            
            filter_languages = user_filter.get("languages", [])
            if filter_languages:
                candidate_languages = candidate.get("languages", [])
                if not any(lang in candidate_languages for lang in filter_languages):
                    continue
        
        return candidate
    
    return None


@router.callback_query(F.data == "feed")
async def show_feed(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ Сначала нужно зарегистрироваться!\nИспользуйте /start",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    user_filter = await get_filter_by_user(callback.from_user.id)
    candidate = await get_next_candidate(callback.from_user.id, user_filter)
    
    if not candidate:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Изменить фильтры", callback_data="settings")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            "😔 <b>Кандидаты закончились!</b>\n\n"
            "Попробуйте изменить фильтры или зайдите позже.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()
        return
    
    await state.update_data(current_candidate_id=candidate.get("user_id"))
    
    card_text = await format_user_card(candidate)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👎 Пропустить", callback_data="swipe_left"),
            InlineKeyboardButton(text="💚 Лайк", callback_data="swipe_right")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    photo_id = candidate.get("photo_id")
    if photo_id:
        await callback.message.delete()
        await callback.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=photo_id,
            caption=card_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(card_text, parse_mode="HTML", reply_markup=keyboard)
    
    await callback.answer()


@router.callback_query(F.data == "swipe_left")
async def swipe_left(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    candidate_id = data.get("current_candidate_id")
    
    if candidate_id:
        await create_match(callback.from_user.id, candidate_id, "skipped")
    
    await callback.answer()
    
    # Удаляем предыдущее сообщение и вызываем show_feed заново
    try:
        await callback.message.delete()
    except:
        pass
    
    # Создаём новое сообщение для следующего кандидата
    user = await get_user_by_id(callback.from_user.id)
    if not user:
        return
    
    user_filter = await get_filter_by_user(callback.from_user.id)
    candidate = await get_next_candidate(callback.from_user.id, user_filter)
    
    if not candidate:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Изменить фильтры", callback_data="settings")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.answer(
            "😔 <b>Кандидаты закончились!</b>\n\n"
            "Попробуйте изменить фильтры или зайдите позже.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return
    
    await state.update_data(current_candidate_id=candidate.get("user_id"))
    
    card_text = await format_user_card(candidate)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👎 Пропустить", callback_data="swipe_left"),
            InlineKeyboardButton(text="💚 Лайк", callback_data="swipe_right")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    photo_id = candidate.get("photo_id")
    if photo_id:
        await callback.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=photo_id,
            caption=card_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(card_text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "swipe_right")
async def swipe_right(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    candidate_id = data.get("current_candidate_id")
    
    if not candidate_id:
        await callback.answer("Ошибка! Кандидат не найден.", show_alert=True)
        return
    
    user = await get_user_by_id(callback.from_user.id)
    candidate = await get_user_by_id(candidate_id)
    
    common_games = set(user.get("games", {}).keys()) & set(candidate.get("games", {}).keys())
    game_name = list(common_games)[0] if common_games else "общие интересы"
    
    # Проверяем, есть ли уже лайк от кандидата к текущему пользователю
    from database.matches import matches_collection
    existing_like = await matches_collection.find_one({
        "user_id_1": candidate_id,
        "user_id_2": callback.from_user.id,
        "status": "pending"
    })
    
    if existing_like:
        # Взаимный лайк! Обновляем статус на accepted
        await matches_collection.update_one(
            {"_id": existing_like["_id"]},
            {"$set": {"status": "accepted", "matched_at": datetime.now()}}
        )
        await callback.answer("🎉 Это матч! Вы понравились друг другу!", show_alert=True)
    else:
        # Создаём новый лайк от текущего пользователя
        match = await create_match(callback.from_user.id, candidate_id, game_name)
        if match:
            await callback.answer("✅ Лайк отправлен!", show_alert=False)
        else:
            await callback.answer("⚠️ Вы уже взаимодействовали с этим пользователем", show_alert=True)
    
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass
    
    # Создаём новое сообщение для следующего кандидата
    user_filter = await get_filter_by_user(callback.from_user.id)
    next_candidate = await get_next_candidate(callback.from_user.id, user_filter)
    
    if not next_candidate:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Изменить фильтры", callback_data="settings")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.answer(
            "😔 <b>Кандидаты закончились!</b>\n\n"
            "Попробуйте изменить фильтры или зайдите позже.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return
    
    await state.update_data(current_candidate_id=next_candidate.get("user_id"))
    
    card_text = await format_user_card(next_candidate)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👎 Пропустить", callback_data="swipe_left"),
            InlineKeyboardButton(text="💚 Лайк", callback_data="swipe_right")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    photo_id = next_candidate.get("photo_id")
    if photo_id:
        await callback.bot.send_photo(
            chat_id=callback.from_user.id,
            photo=photo_id,
            caption=card_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(card_text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "my_matches")
async def show_my_matches(callback: CallbackQuery, state: FSMContext):
    from database.matches import get_accepted_matches
    matches = await get_accepted_matches(callback.from_user.id)
    
    if not matches:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📰 Смотреть ленту", callback_data="feed")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            "📭 <b>У вас пока нет взаимных матчей</b>\n\n"
            "Начните смотреть ленту и ставить лайки!",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()
        return
    
    text = "🎯 <b>Ваши взаимные матчи:</b>\n\n"
    
    for idx, match in enumerate(matches[:10], 1):
        partner_id = match.get("user_id_2") if match.get("user_id_1") == callback.from_user.id else match.get("user_id_1")
        partner = await get_user_by_id(partner_id)
        
        if partner:
            text += f"{idx}. 💚 <b>{partner.get('nickname')}</b> ({partner.get('age')})\n"
            text += f"   Игра: {match.get('game_name')}\n"
            text += f"   @{partner.get('username', 'нет username')}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📰 Вернуться к ленте", callback_data="feed")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.users import get_user_by_id, get_all_active_users
from database.matches import create_match, get_user_matches
from database.filtrs import get_filter_by_user

router = Router()


def format_user_card(user):
    games_str = " | ".join([f"{game}" for game in user.get("games", {}).keys()])
    gender_emoji = "👨" if user.get("gender") == "male" else "👩"
    
    text = (
        f"{gender_emoji} <b>{user.get('nickname')}</b>, {user.get('age')}\n\n"
        f"🎮 <b>Игры:</b> {games_str}\n\n"
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
        if match.get("user_id_1") == current_user_id:
            viewed_ids.add(match.get("user_id_2"))
        else:
            viewed_ids.add(match.get("user_id_1"))
    
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
    
    card_text = format_user_card(candidate)
    
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
    
    await show_feed(callback, state)


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
    
    match = await create_match(callback.from_user.id, candidate_id, game_name)
    
    if match:
        await callback.answer("✅ Лайк отправлен!", show_alert=False)
    else:
        await callback.answer("⚠️ Вы уже взаимодействовали с этим пользователем", show_alert=True)
    
    await show_feed(callback, state)


@router.callback_query(F.data == "my_matches")
async def show_my_matches(callback: CallbackQuery, state: FSMContext):
    matches = await get_user_matches(callback.from_user.id)
    
    if not matches:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📰 Смотреть ленту", callback_data="feed")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            "📭 <b>У вас пока нет матчей</b>\n\n"
            "Начните смотреть ленту и ставить лайки!",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()
        return
    
    text = "🎯 <b>Ваши матчи:</b>\n\n"
    
    for idx, match in enumerate(matches[:10], 1):
        partner_id = match.get("user_id_2") if match.get("user_id_1") == callback.from_user.id else match.get("user_id_1")
        partner = await get_user_by_id(partner_id)
        
        if partner:
            status_emoji = {
                "pending": "⏳",
                "accepted": "✅",
                "rejected": "❌",
                "skipped": "👎"
            }.get(match.get("status"), "❓")
            
            text += f"{idx}. {status_emoji} <b>{partner.get('nickname')}</b> ({partner.get('age')})\n"
            text += f"   Игра: {match.get('game_name')}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📰 Вернуться к ленте", callback_data="feed")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

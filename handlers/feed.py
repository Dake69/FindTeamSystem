from aiogram import Router, F
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database.users import get_user_by_id, get_all_active_users, update_user
from database.matches import create_match, get_user_matches, get_incoming_likes, matches_collection
from database.filtrs import get_filter_by_user
from database.user_settings import get_settings_by_user, ensure_settings
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
import logging

async def safe_send_photo(bot: Bot, chat_id, photo_id, caption, parse_mode="HTML", reply_markup=None, db_user_id=None):
    try:
        await bot.send_photo(chat_id=chat_id, photo=photo_id, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        logging.exception("Failed to send photo, falling back to text message: %s", e)
        # Only clear photo_id when the error explicitly indicates an invalid file identifier or URL
        err_msg = str(e).lower()
        should_clear = False
        if db_user_id and ("wrong file identifier" in err_msg or "http url specified" in err_msg or "file identifier" in err_msg):
            should_clear = True

        if should_clear:
            try:
                await update_user(db_user_id, {"photo_id": None})
                logging.info("Cleared photo_id for user %s due to invalid file identifier", db_user_id)
            except Exception:
                logging.exception("Failed to clear photo_id for user %s", db_user_id)
        try:
            await bot.send_message(chat_id=chat_id, text=caption, parse_mode=parse_mode, reply_markup=reply_markup)
        except Exception:
            logging.exception("Also failed to send fallback text message when photo failed")

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
        status = match.get("status")
        if status == "accepted":
            if match.get("user_id_1") == current_user_id:
                viewed_ids.add(match.get("user_id_2"))
            else:
                viewed_ids.add(match.get("user_id_1"))
            continue

        # If skip was marked to exclude both, exclude both users
        if status == "skipped" and match.get("exclude_both"):
            other = match.get("user_id_2") if match.get("user_id_1") == current_user_id else match.get("user_id_1")
            viewed_ids.add(match.get("user_id_1"))
            if other:
                viewed_ids.add(other)
            continue

        # Exclude skipped only if the current user is the one who skipped (outgoing skip)
        if status == "skipped" and match.get("user_id_1") == current_user_id:
            viewed_ids.add(match.get("user_id_2"))
            continue

        # Exclude outgoing pending (users the current user already liked)
        if status == "pending" and match.get("user_id_1") == current_user_id:
            viewed_ids.add(match.get("user_id_2"))

    try:
        incoming = await get_incoming_likes(current_user_id)
    except Exception:
        incoming = []
    for match in incoming:
        candidate_id = match.get("user_id_1")
        if not candidate_id or candidate_id == current_user_id:
            continue
        if candidate_id in viewed_ids:
            continue
        candidate = await get_user_by_id(candidate_id)
        if not candidate:
            continue
        return candidate

    current_user = await get_user_by_id(current_user_id)
    current_games = set(current_user.get("games", {}).keys()) if current_user else set()

    def passes_filter(candidate, user_filter):
        if not user_filter:
            return True
        filter_games = user_filter.get("games", [])
        if filter_games:
            candidate_games = set(candidate.get("games", {}).keys())
            if not any(g in candidate_games for g in filter_games):
                return False
        filter_gender = user_filter.get("gender", "any")
        if filter_gender != "any" and candidate.get("gender") != filter_gender:
            return False
        age_min = user_filter.get("age_min")
        age_max = user_filter.get("age_max")
        candidate_age = candidate.get("age")
        if age_min and candidate_age < age_min:
            return False
        if age_max and candidate_age > age_max:
            return False
        filter_languages = user_filter.get("languages", [])
        if filter_languages:
            candidate_languages = candidate.get("languages", [])
            if not any(lang in candidate_languages for lang in filter_languages):
                return False
        return True

    for candidate in all_users:
        cid = candidate.get("user_id")
        if not cid or cid in viewed_ids or cid == current_user_id:
            continue
        candidate_games = set(candidate.get("games", {}).keys())
        if current_games and candidate_games & current_games:
            if passes_filter(candidate, user_filter):
                return candidate

    for candidate in all_users:
        cid = candidate.get("user_id")
        if not cid or cid in viewed_ids or cid == current_user_id:
            continue
        if passes_filter(candidate, user_filter):
            return candidate

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
        await safe_send_photo(callback.bot, callback.from_user.id, photo_id, card_text, "HTML", keyboard, candidate.get("user_id"))
    else:
        await callback.message.edit_text(card_text, parse_mode="HTML", reply_markup=keyboard)

    await callback.answer()


@router.callback_query(F.data == "swipe_left")
async def swipe_left(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    candidate_id = data.get("current_candidate_id")

    if candidate_id:
        try:
            existing = await matches_collection.find_one({
                "$or": [
                    {"user_id_1": callback.from_user.id, "user_id_2": candidate_id},
                    {"user_id_1": candidate_id, "user_id_2": callback.from_user.id}
                ]
            })
        except Exception:
            existing = None

        if existing:
            if existing.get("status") == "pending" and existing.get("user_id_1") == candidate_id:
                # Current user is skipping an incoming pending like.
                # Normalize the record to be an outgoing skip from the current user
                try:
                    # Mark skipped and exclude both users from future feeds for this pair
                    await matches_collection.update_one({"_id": existing["_id"]}, {"$set": {"status": "skipped", "user_id_1": callback.from_user.id, "user_id_2": candidate_id, "exclude_both": True}})
                except Exception:
                    # Fallback: if updating direction fails, at least mark as skipped
                    await matches_collection.update_one({"_id": existing["_id"]}, {"$set": {"status": "skipped"}})
            else:
                pass
        else:
            await create_match(callback.from_user.id, candidate_id, game_name=None, status="skipped")

        try:
            docs = await matches_collection.find({
                "$or": [
                    {"user_id_1": callback.from_user.id, "user_id_2": candidate_id},
                    {"user_id_1": candidate_id, "user_id_2": callback.from_user.id}
                ]
            }).to_list(length=10)
            logging.debug("Matches between %s and %s after swipe_left: %s", callback.from_user.id, candidate_id, docs)
        except Exception:
            logging.exception("Failed to fetch matches for debug after swipe_left")

    await callback.answer()

    try:
        await callback.message.delete()
    except:
        pass

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
        await safe_send_photo(callback.bot, callback.from_user.id, photo_id, card_text, "HTML", keyboard, candidate.get("user_id"))
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

    existing_like = await matches_collection.find_one({
        "user_id_1": candidate_id,
        "user_id_2": callback.from_user.id,
        "status": "pending"
    })

    if existing_like:
        await matches_collection.update_one(
            {"_id": existing_like["_id"]},
            {"$set": {"status": "accepted", "matched_at": datetime.utcnow()}}
        )
        try:
            settings_candidate = await get_settings_by_user(candidate_id)
            settings_user = await get_settings_by_user(callback.from_user.id)

            nick_user = user.get("nickname") or callback.from_user.username or str(callback.from_user.id)
            nick_candidate = candidate.get("nickname") or candidate.get("username") or str(candidate_id)

            if settings_candidate and settings_candidate.get("notify_on_match"):
                try:
                    await callback.bot.send_message(
                        chat_id=candidate_id,
                        text=(
                            f"🎉 Это метч!\n"
                            f"Вы и {nick_user} понравились друг другу!\n\n"
                            "Телеграмм нового друга можно посмотреть во вкладке \"мои метчи\""
                        ),
                        disable_notification=not settings_candidate.get("notify_sound", True)
                    )
                except Exception:
                    pass

            if settings_user and settings_user.get("notify_on_match"):
                try:
                    await callback.bot.send_message(
                        chat_id=callback.from_user.id,
                        text=(
                            f"🎉 Это метч!\n"
                            f"Вы и {nick_candidate} понравились друг другу!\n\n"
                            "Телеграмм нового друга можно посмотреть во вкладке \"мои метчи\""
                        ),
                        disable_notification=not settings_user.get("notify_sound", True)
                    )
                except Exception:
                    pass
        except Exception:
            pass
        await callback.answer("🎉 Это метч! Вы понравились друг другу!", show_alert=True)
        try:
            docs = await matches_collection.find({
                "$or": [
                    {"user_id_1": callback.from_user.id, "user_id_2": candidate_id},
                    {"user_id_1": candidate_id, "user_id_2": callback.from_user.id}
                ]
            }).to_list(length=10)
            logging.debug("Matches between %s and %s after accept: %s", callback.from_user.id, candidate_id, docs)
        except Exception:
            logging.exception("Failed to fetch matches for debug after accept")
    else:
        match = await create_match(callback.from_user.id, candidate_id, game_name)
        if match:
            await callback.answer("✅ Лайк отправлен!", show_alert=False)
            try:
                settings_recipient = await get_settings_by_user(candidate_id)
                if settings_recipient and settings_recipient.get("notify_on_like"):
                    liker_name = user.get("nickname") or callback.from_user.username or str(callback.from_user.id)
                    try:
                        await callback.bot.send_message(
                            chat_id=candidate_id,
                            text=(
                                f"💚 {liker_name} поставил(а) вам лайк!\n\n"
                                "Этот пользователь будет следующим в вашей ленте."
                            ),
                            disable_notification=not settings_recipient.get("notify_sound", True),
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text="📰 Открыть ленту", callback_data="feed")]
                            ])
                        )
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            await callback.answer("⚠️ Вы уже взаимодействовали с этим пользователем", show_alert=True)
            try:
                docs = await matches_collection.find({
                    "$or": [
                        {"user_id_1": callback.from_user.id, "user_id_2": candidate_id},
                        {"user_id_1": candidate_id, "user_id_2": callback.from_user.id}
                    ]
                }).to_list(length=10)
                logging.debug("Matches between %s and %s when create_match returned None: %s", callback.from_user.id, candidate_id, docs)
            except Exception:
                logging.exception("Failed to fetch matches for debug when create_match returned None")

    try:
        await callback.message.delete()
    except:
        pass

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
        await safe_send_photo(callback.bot, callback.from_user.id, photo_id, card_text, "HTML", keyboard, next_candidate.get("user_id"))
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
            "📭 <b>У вас пока нет взаимных метчей</b>\n\n"
            "Начните смотреть ленту и ставить лайки!",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()
        return

    text = "🎯 <b>Ваши взаимные метчи:</b>\n\n"

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

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except TelegramBadRequest as e:
        msg = str(e)
        if "message is not modified" in msg:
            pass
        else:
            raise
    await callback.answer()

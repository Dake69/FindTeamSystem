from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


admin_panel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🕹 Управление играми", callback_data="admin_games")],
        [InlineKeyboardButton(text="🌐 Управление языками", callback_data="admin_languages")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users")],
    ]
)

admin_games_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить игру", callback_data="admin_add_game"),
        InlineKeyboardButton(text="🔍 Все игры", callback_data="admin_show_games")],
        [InlineKeyboardButton(text="➕ Добавить жанр", callback_data="admin_add_genre"),
        InlineKeyboardButton(text="🔍 Все жанры", callback_data="admin_show_genres")],
        [InlineKeyboardButton(text="⬅️ Назад в админ-панель", callback_data="admin_panel")]
    ]
)

def get_game_manage_kb(game_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_game_{game_id}")],
            [InlineKeyboardButton(text="🏆 Редактировать ранги", callback_data=f"admin_edit_ranks_{game_id}")],
            [InlineKeyboardButton(text="❌ Удалить игру", callback_data=f"admin_delete_game_{game_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку игр", callback_data="admin_show_games")]
        ]
    )

def get_genre_manage_kb(genre_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_genre_{genre_id}")],
            [InlineKeyboardButton(text="❌ Удалить жанр", callback_data=f"admin_delete_genre_{genre_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку жанров", callback_data="admin_show_genres")]
        ]
    )

def get_cancel_to_games_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_games")]
        ]
    )

admin_languages_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить язык", callback_data="admin_add_language")],
        [InlineKeyboardButton(text="🌐 Все языки", callback_data="admin_show_languages")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]
    ]
)

def get_cancel_to_languages_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_languages")]
        ]
    )

def get_language_manage_kb(language_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_language_{language_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete_language_{language_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_show_languages")]
        ]
    )


def get_user_manage_kb(user_id, is_active=True, is_banned=False):
    buttons = []
    if is_banned:
        buttons.append([InlineKeyboardButton(text="♻️ Разбанить", callback_data=f"admin_unban_{user_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="❌ Забанить", callback_data=f"admin_ban_{user_id}")])

    if is_active:
        buttons.append([InlineKeyboardButton(text="🔕 Сделать неактивным", callback_data=f"admin_toggle_active_{user_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🔔 Сделать активным", callback_data=f"admin_toggle_active_{user_id}")])

    buttons.append([InlineKeyboardButton(text="✉️ Отправить предупреждение", callback_data=f"admin_warn_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_users")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
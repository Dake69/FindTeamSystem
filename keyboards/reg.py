from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

game_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Game 1", callback_data="game_1")],
    [InlineKeyboardButton(text="Game 2", callback_data="game_2")],
])





contact_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Share contact", request_contact=True)],
], resize_keyboard=True, one_time_keyboard=True)

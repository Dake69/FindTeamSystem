from aiogram.fsm.state import StatesGroup, State

class RegistrationInline(StatesGroup):
    full_name = State()
    nickname = State()
    phone = State()
    game = State()
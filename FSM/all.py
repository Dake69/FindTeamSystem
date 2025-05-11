from aiogram.fsm.state import StatesGroup, State

class RegistrationInline(StatesGroup):
    full_name = State()
    nickname = State()
    phone = State()
    game = State()

class AddGameFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_genre = State()
    waiting_for_description = State()
    waiting_for_ranks_count = State()
    waiting_for_rank_name = State()


class EditGameFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_genre = State()
    waiting_for_description = State()
    

class EditRanksFSM(StatesGroup):
    waiting_for_ranks_count = State()
    waiting_for_rank_name = State()

class AddGenreFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    
class EditGenreFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
from aiogram.fsm.state import StatesGroup, State

class RegistrationInline(StatesGroup):
    full_name = State()
    wait_for_contact = State()
    nickname = State()
    age = State()
    gender = State()
    about = State()
    photo = State()
    game = State()
    rank = State()
    language = State()

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

class AddLanguageFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_code = State()

class EditLanguageFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_code = State()

class FilterFSM(StatesGroup):
    games = State()     
    ranks = State()     
    gender = State()      
    age = State()
    languages = State()

class EditProfileFSM(StatesGroup):
    edit_photo = State()
    edit_fullname = State()
    edit_nickname = State()
    edit_about = State()
    edit_games = State()
    edit_rank = State()


class AdminWarnFSM(StatesGroup):
    waiting_for_text = State()

"""
ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ API

=== СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ ===

from models import User, Gender

user = User(
    user_id=12345,
    full_name="Иван Иванов",
    nickname="IvanGamer",
    age=25,
    gender=Gender.MALE,
    about="Люблю играть в шутеры",
    phone="+79001234567",
    games={"CS:GO": "Global Elite", "Valorant": "Immortal"},
    username="ivan_gamer"
)

Через сервис:
result = await user_service.register_user(
    user_id=12345,
    full_name="Иван Иванов",
    nickname="IvanGamer",
    age=25,
    gender=Gender.MALE,
    about="Люблю играть в шутеры",
    phone="+79001234567",
    games={"CS:GO": "Global Elite"},
)

=== СОЗДАНИЕ ИГРЫ ===

from models import Game

game = Game(
    game_name="CS:GO",
    genre="FPS",
    description="Counter-Strike: Global Offensive",
    ranks=["Silver", "Gold Nova", "Master Guardian", "Legendary Eagle", "Global Elite"]
)

Через сервис:
result = await game_service.create_game(
    game_name="CS:GO",
    genre="FPS",
    ranks=["Silver", "Gold", "Global Elite"]
)

=== СОЗДАНИЕ ФИЛЬТРА ===

from models import UserFilter, Gender, AgeRange

user_filter = UserFilter(
    user_id=12345,
    games=["CS:GO", "Valorant"],
    gender=Gender.ANY,
    age_range=AgeRange(min_age=18, max_age=30),
    games_ranks={"CS:GO": "Global Elite"}
)

Через сервис:
filter = await filter_service.create_or_update_filter(
    user_id=12345,
    games=["CS:GO"],
    gender=Gender.MALE,
    min_age=18,
    max_age=30
)

=== СИСТЕМА МАТЧИНГА ===

Получить следующего кандидата:
candidate = await match_service.get_next_candidate(
    user_id=12345,
    user_filter=user_filter
)

Создать матч:
match = await match_service.create_match(
    user_id_1=12345,
    user_id_2=67890,
    game_name="CS:GO"
)

Принять матч:
success = await match_service.accept_match(match_id)

=== ПОСТРОЕНИЕ КЛАВИАТУР ===

from ui import InlineKeyboardBuilder, DynamicInlineKeyboard

Простая клавиатура:
keyboard = InlineKeyboardBuilder()
    .add_button("Нравится", "like_12345")
    .add_button("Пропустить", "skip_12345")
    .build()

Клавиатура выбора:
keyboard = DynamicInlineKeyboard.create_selection_keyboard(
    items=[{"game_name": "CS:GO"}, {"game_name": "Valorant"}],
    selected_items=["CS:GO"],
    item_key="game_name",
    callback_prefix="game",
    done_callback="games_done"
)

Главное меню:
keyboard = DynamicInlineKeyboard.create_main_menu()

=== ФОРМАТИРОВАНИЕ ===

from ui import UserProfileFormatter

Полный профиль:
text = UserProfileFormatter.format_profile(user)

Карточка для ленты:
text = UserProfileFormatter.format_profile_card(user)

=== РАБОТА С РЕПОЗИТОРИЯМИ ===

Поиск пользователя:
user = await user_repository.find_by_user_id(12345)
user = await user_repository.find_by_phone("+79001234567")
user = await user_repository.find_by_nickname("IvanGamer")

Обновление:
user.deactivate()
await user_repository.update(user)

Получить всех активных пользователей:
users = await user_repository.find_active_users(skip=0, limit=50)

=== ПОЛЬЗОВАТЕЛЬСКИЕ СТРАТЕГИИ МАТЧИНГА ===

from services.matching import MatchingStrategy

class CustomMatchingStrategy(MatchingStrategy):
    def calculate_score(self, user, candidate, filter):
        score = 0.0
        
        if user.language == candidate.language:
            score += 20.0
        
        age_diff = abs(user.age - candidate.age)
        if age_diff < 5:
            score += 15.0
        elif age_diff < 10:
            score += 10.0
        
        return score
    
    def is_match(self, user, candidate, filter):
        return True

Использование:
strategy = CompositeMatchingStrategy([
    GameBasedMatchingStrategy(),
    FilterBasedMatchingStrategy(),
    CustomMatchingStrategy()
])
matching_engine = MatchingEngine(strategy)

=== РАСШИРЕНИЕ HANDLER ===

class ProfileHandler:
    def __init__(self, router, user_service, formatter):
        self._router = router
        self._user_service = user_service
        self._formatter = formatter
        self._register_handlers()
    
    def _register_handlers(self):
        self._router.callback_query(F.data == "profile")(self._show_profile)
    
    async def _show_profile(self, callback: CallbackQuery, state: FSMContext):
        user = await self._user_service.get_user_by_id(callback.from_user.id)
        text = self._formatter.format_profile(user)
        
        keyboard = InlineKeyboardBuilder()
            .add_button("Редактировать", "edit_profile")
            .add_button("Назад", "main_menu")
            .build()
        
        await callback.message.edit_text(text, reply_markup=keyboard)

=== DEPENDENCY INJECTION ===

container = ServiceContainer()
await container.initialize()

user_service = container.user_service
game_service = container.game_service
match_service = container.match_service

handler = RegistrationHandler(
    router=router,
    user_service=container.user_service,
    game_service=container.game_service,
    filter_service=container.filter_service,
    formatter=container.user_formatter
)
"""

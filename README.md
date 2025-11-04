# FindTeamSystem

Telegram-бот для поиска тиммейтов в играх.

## Структура проекта

```
FindTeamSystem/
├── database/           # Работа с MongoDB
│   ├── db.py          # Подключение к БД
│   ├── users.py       # Работа с пользователями
│   ├── games.py       # Работа с играми
│   ├── filtrs.py      # Работа с фильтрами
│   ├── matches.py     # Работа с матчами
│   └── language.py    # Работа с языками
├── handlers/          # Обработчики команд бота
│   ├── reg.py        # Регистрация
│   ├── slider.py     # Лента
│   ├── settings.py   # Настройки
│   └── admin/        # Админ-панель
├── keyboards/         # Клавиатуры
├── FSM/              # Состояния FSM
├── config.py         # Конфигурация
└── main.py          # Точка входа
```

## База данных

MongoDB коллекции:
- `users` - пользователи
- `games` - игры
- `matches` - матчи
- `filters` - фильтры
- `languages` - языки

## Установка

```bash
pip install -r requirements.txt
```

## Конфигурация

Файл `.env`:
```
BOT_TOKEN
MONGODB_URI
```

## Запуск

```bash
python main.py
```

## Архитектура

Проект реализован с использованием принципов ООП, SOLID и паттернов проектирования:

### Структура проекта

```
FindTeamSystem/
├── models/              # Доменные модели (User, Game, Match, Filter)
├── repositories/        # Repository паттерн для работы с БД
├── services/           # Бизнес-логика и сервисы
├── handlers_new/       # Обработчики команд бота (новая архитектура)
├── ui/                 # UI компоненты (клавиатуры, форматтеры)
├── FSM/                # Состояния для aiogram FSM
├── config.py           # Конфигурация приложения
├── container.py        # DI контейнер для управления зависимостями
└── main.py            # Точка входа
```

### Основные компоненты

#### Models
- `BaseModel` / `BaseDocument` - абстрактные базовые классы
- `User` - модель пользователя с инкапсуляцией данных
- `Game` - модель игры с рангами
- `Match` - модель матча между пользователями
- `UserFilter` - модель фильтров для поиска

#### Repositories
- `BaseRepository<T>` - generic базовый репозиторий
- `UserRepository`, `GameRepository`, `MatchRepository`, `FilterRepository`

#### Services
- `UserService` - управление пользователями
- `GameService` - управление играми
- `MatchService` - создание и управление матчами
- `FilterService` - работа с фильтрами поиска
- `MatchingEngine` - алгоритм подбора с Strategy паттерном

#### UI Layer
- `InlineKeyboardBuilder` - построитель инлайн-клавиатур
- `DynamicInlineKeyboard` - динамическая генерация клавиатур
- `UserProfileFormatter` - форматирование профилей
- `MatchFormatter` - форматирование матчей

## Технологии

- Python 3.10+
- aiogram 3.x
- MongoDB (motor)
- Асинхронное программирование

## Установка

```bash
pip install -r requirements.txt
```

## Конфигурация

Создайте файл `.env` в корне проекта:
```
BOT_TOKEN=your_telegram_bot_token
MONGODB_URI=mongodb+srv://...
```

## Запуск

```bash
python main.py
```

## Особенности реализации

### ООП принципы
- **Инкапсуляция**: все поля моделей приватные с геттерами
- **Наследование**: иерархия моделей от BaseDocument
- **Полиморфизм**: Strategy паттерн в MatchingEngine
- **Абстракция**: абстрактные классы для Repository и KeyboardBuilder

### Паттерны проектирования
- Repository Pattern
- Strategy Pattern (для алгоритмов матчинга)
- Builder Pattern (для клавиатур)
- Dependency Injection (ServiceContainer)
- Composite Pattern (CompositeMatchingStrategy)

### Система матчинга
Использует композитную стратегию:
- `GameBasedMatchingStrategy` - подбор по играм и рангам
- `FilterBasedMatchingStrategy` - фильтрация по полу и возрасту
- Оценка совместимости с расчетом score

## База данных

Коллекции MongoDB:
- `users` - пользователи
- `games` - игры с рангами
- `matches` - история матчей
- `filters` - пользовательские фильтры


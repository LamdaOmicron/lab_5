## 13. Документация

# Лабораторная работа №2: RESTful API для управления персонажами

# Лабораторная работа №4: Автоматизированное документирование REST API с использованием OpenAPI (Swagger)

## Описание проекта

RESTful API для управления игровыми персонажами (на примере Pathfinder 2e) с полной JWT аутентификацией, OAuth поддержкой (Yandex/VK), и автоматической Swagger документацией. Реализован полный CRUD с мягким удалением (soft delete) и пагинацией. Проект использует Django + Django REST Framework, PostgreSQL в Docker.

## Технологии

- Python 3.12
- Django 4.2
- Django REST Framework 3.14
- drf-spectacular (OpenAPI/Swagger)
- PostgreSQL 16
- Docker & Docker Compose
- JWT аутентификация
- OAuth 2.0 (Yandex, VK)

## Запуск проекта

### Предварительные требования

- Установленный Docker и Docker Compose
- (Опционально) Git для клонирования репозитория

### Шаги для запуска

1. **Клонировать репозиторий**:
   ```bash
   git clone <url-репозитория>
   cd lab_2
   ```

2. **Создать файл `.env`** на основе `.env.example` (см. ниже).

3. **Запустить контейнеры**:
   ```bash
   docker-compose up --build
   ```
   - При первом запуске автоматически выполнятся миграции.
   - API будет доступно по адресу: `http://localhost:4200/api/characters/`
   - **Swagger документация** доступна по адресу: `http://localhost:4200/api/docs/` (только в режиме разработки)

4. **Остановить контейнеры**:
   ```bash
   docker-compose down
   ```

## Переменные окружения

Создайте файл `.env` в корне проекта со следующим содержимым (скопируйте из `.env.example` и при необходимости измените):

```env
# PostgreSQL
DB_USER=student
DB_PASSWORD=student_secure_password
DB_NAME=wp_labs
DB_HOST=postgres
DB_PORT=5432

# Приложение
APP_PORT=4200

# Окружение (development или production)
# Установите 'production' для отключения Swagger документации
NODE_ENV=development

# JWT Configuration
JWT_ACCESS_SECRET=super_secret_access_key_change_in_prod
JWT_REFRESH_SECRET=super_secret_refresh_key_change_in_prod
JWT_ACCESS_EXPIRATION=15m
JWT_REFRESH_EXPIRATION=7d

# OAuth Provider Configuration
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
CALLBACK_URL=http://localhost:4200/auth/yandex/callback
```

**Примечание:** файл `.env.example` должен быть в репозитории, а сам `.env` добавлен в `.gitignore`.

## API Endpoints
http://localhost:8000/admin/login/?next=/admin/
Если суперпользователь(АДМИН!!!!) ещё не создан, выполните в терминале команду: docker compose exec app python manage.py createsuperuser


### Базовый URL: `http://localhost:4200`

#### Auth (Аутентификация)

| Метод   | URI                          | Описание                             | Статус успеха | Требует авторизации |
|---------|------------------------------|--------------------------------------|---------------|---------------------|
| POST    | `/auth/register/`            | Регистрация нового пользователя      | 201 Created   | Нет                 |
| POST    | `/auth/login/`               | Вход пользователя                    | 200 OK        | Нет                 |
| POST    | `/auth/refresh/`             | Обновление JWT токенов               | 200 OK        | Нет (использует cookie) |
| GET     | `/auth/whoami/`              | Проверка авторизации                 | 200 OK        | Да                  |
| POST    | `/auth/logout/`              | Выход из текущей сессии              | 200 OK        | Да                  |
| POST    | `/auth/logout-all/`          | Выход из всех сессий                 | 200 OK        | Да                  |
| GET     | `/auth/oauth/<provider>/`    | Инициация OAuth входа                | 200 OK        | Нет                 |
| GET     | `/auth/oauth/<provider>/callback/` | OAuth callback           | 302 Redirect  | Нет                 |
| POST    | `/auth/forgot-password/`     | Запрос сброса пароля                 | 200 OK        | Нет                 |
| POST    | `/auth/reset-password/`      | Сброс пароля                         | 200 OK        | Нет                 |

#### Characters (Персонажи)

Базовый URL: `http://localhost:4200/api/characters/`

| Метод   | URI                      | Описание                             | Статус успеха | Требует авторизации |
|---------|--------------------------|--------------------------------------|---------------|---------------------|
| GET     | `/`                      | Список персонажей (с пагинацией)     | 200 OK        | Нет                 |
| POST    | `/`                      | Создание нового персонажа            | 201 Created   | Нет                 |
| GET     | `/<uuid:id>/`            | Получение персонажа по ID            | 200 OK        | Нет                 |
| PUT     | `/<uuid:id>/`            | Полное обновление персонажа          | 200 OK        | Нет                 |
| PATCH   | `/<uuid:id>/`            | Частичное обновление персонажа       | 200 OK        | Нет                 |
| DELETE  | `/<uuid:id>/`            | Мягкое удаление персонажа            | 204 No Content| Нет                 |

### Пагинация

Параметры передаются в query string:
- `page` – номер страницы (по умолчанию 1)
- `limit` – количество записей на странице (по умолчанию 10, максимум 100)

**Пример запроса**:
```
GET /api/characters/?page=2&limit=20
```

**Ответ**:
```json
{
  "data": [
    { /* объект персонажа */ }
  ],
  "meta": {
    "total": 42,
    "page": 2,
    "limit": 20,
    "totalPages": 3
  }
}
```

## Swagger документация

Документация генерируется автоматически на основе кода приложения с использованием библиотеки `drf-spectacular`.

### Доступ к документации

- **Development режим** (`NODE_ENV=development`): Документация доступна по адресу `http://localhost:4200/api/docs/`
- **Production режим** (`NODE_ENV=production`): Документация **недоступна** (возвращает 404)

### Функции Swagger UI

- Интерактивное тестирование всех эндпоинтов
- Просмотр схем запросов и ответов с примерами
- Авторизация через JWT (токен передается в cookies)
- Группировка эндпоинтов по тегам (Auth, Characters)
- Описание всех возможных статусов ответа (200, 201, 400, 401, 403, 404)

### Безопасность в документации

- Чувствительные данные (пароли, соли, refresh токены) скрыты из схем ответов с помощью `write_only=True`
- Защищенные эндпоинты помечены значком замка 🔒
- Для тестирования защищенных эндпоинтов необходимо сначала выполнить login через `/auth/login/`

## Миграции

Миграции запускаются автоматически при старте контейнера (команда `python manage.py migrate` в `CMD` Dockerfile). Если необходимо выполнить миграции вручную:

```bash
docker exec -it wp_labs_app python manage.py migrate
```

## Тестирование

Для запуска тестов (внутри контейнера или локально с PostgreSQL):

```bash
docker exec -it wp_labs_app python manage.py test characters
```

Все тесты должны проходить успешно.

## Структура проекта

```
lab_2/
├── characters/               # приложение персонажей
│   ├── models.py            # модель Character
│   ├── views.py             # контроллеры с @extend_schema
│   ├── serializers.py       # сериализаторы с примерами
│   ├── services.py          # бизнес-логика
│   ├── exceptions.py        # кастомный обработчик ошибок
│   └── tests.py             # тесты
├── auth_app/                 # приложение аутентификации
│   ├── views.py             # контроллеры авторизации
│   ├── dto.py               # DTO/серриализаторы
│   ├── services.py          # AuthService
│   └── jwt_utils.py         # утилиты JWT
├── users/                    # приложение пользователей
│   └── models.py            # модель User
├── myproject/               # настройки Django
│   ├── settings.py          # конфигурация + SPECTACULAR_SETTINGS
│   └── urls.py              # маршруты + Swagger routes
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Ссылки

- [Django REST Framework](https://www.django-rest-framework.org/)
- [drf-spectacular documentation](https://drf-spectacular.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Docker Compose](https://docs.docker.com/compose/)

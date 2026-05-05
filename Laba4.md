# Лабораторная работа №4

## 
Тема: Автоматизированное документирование REST API с использованием OpenAPI (Swagger)

## Цель работы:

- Изучить спецификацию OpenAPI (ранее Swagger) как стандарт описания веб-сервисов.
- Освоить принципы автоматической генерации документации на основе кода приложения (Code-First подход).
- Научиться аннотировать контроллеры, DTO и модели метаданными для формирования интерактивной документации.
- Реализовать разделение конфигурации документации для сред разработки (Development / Local) и промышленной эксплуатации (Production).
- Настроить отображение схем безопасности (JWT, Cookies) в интерфейсе документации для тестирования защищенных эндпоинтов.
- Закрепить навыки описания примеров запросов, ответов и возможных кодов ошибок.

## Технические требования:

- Наличие интернет-соединения.
- Наличие браузера с инструментами разработчика.
- Наличие [Docker](https://docs.docker.com/desktop/) и [Docker Compose](https://docs.docker.com/compose/install/)
- Наличие настроенного окружения из Лабораторной работы №3 (приложение с авторизацией, CRUD ресурсами, Docker).

## Технические ограничения:

- Инструментарий: Разрешено и рекомендуется использование официальных библиотек для генерации Swagger/OpenAPI документации, соответствующих выбранному стеку. Запрещено ручное написание YAML/JSON файлов спецификации; документация должна собираться автоматически из кода.
- Безопасность документации: Эндпоинт документации (например, `/api/docs`, `/swagger`) должен быть доступен только в режиме разработки (`development` / `local`). В режиме производства (`production`) доступ к документации должен быть заблокирован на уровне приложения или веб-сервера.
- Полнота описания: Все эндпоинты, реализованные в лабораторной работе №2 и №3, должны быть отражены в документации.
- Примеры: Для каждого успешного ответа и основных ошибок (400, 401, 403, 404) должны быть приведены примеры тел ответов (examples).
- Безопасность в UI: Интерфейс Swagger UI должен позволять авторизовываться (вводить JWT токен или использовать Cookies) для тестирования защищенных методов (`/whoami`, CRUD операции).
- Наследование: Работа выполняется над кодом Лабораторной работы №3. Все механизмы аутентификации, OAuth, хеширования и Soft Delete должны оставаться работоспособными.
## Ход работы

### 1. Установка зависимостей и настройка библиотеки

В зависимости от выбранного стека, подключите необходимую библиотеку для генерации OpenAPI спецификации.

- TypeScript (NestJS): Используйте пакет `@nestjs/swagger`. Он автоматически сканирует декораторы контроллеров и DTO.
  - [Документация @nestjs/swagger](https://docs.nestjs.com/openapi/introduction)
- Java (Spring Boot): Используйте зависимость `springdoc-openapi-starter-webmvc-ui` (или `springfox` для старых версий).
  - [Документация springdoc-openapi](https://springdoc.org/)
- Python (FastAPI): Встроенная поддержка Swagger через `Uvicorn` + `FastAPI` (использует `Pydantic`).
  - [Документация FastAPI Swagger](https://fastapi.tiangolo.com/tutorial/metadata/)
- Python (Django): Используйте пакет `drf-spectacular` или `django-rest-swagger` вместе с Django REST Framework.
  - [Документация drf-spectacular](https://drf-spectacular.readthedocs.io/)
- Go (Gin/Fiber): Используйте библиотеку `swaggo/swag` (требует генерации комментариев) или встроенные решения фреймворка (если есть).
  - [Документация swaggo](https://github.com/swaggo/swag)
- PHP (Laravel): Используйте пакет `darkaonline/l5-swagger` или `zircote/swagger-php`.
  - [Документация l5-swagger](https://github.com/DarkaOnLine/l5-swagger)

### 2. Конфигурация окружения и условный запуск

Реализуйте логику, при которой модуль документации инициализируется только если переменная окружения указывает на режим разработки.

1.  Добавьте в файл `.env`:
    ```env
    NODE_ENV=development
    # Или для других языков: 
    # APP_ENV=local
    # SWAGGER_ENABLED=true
    ```
2.  В главном файле запуска приложения (например, `main.ts` в NestJS или `Application.java` в Spring) оберните инициализацию Swagger в условие.

    ```typescript
    if (process.env.NODE_ENV !== "production") {
      const config = new DocumentBuilder()
        .setTitle("Lab Project API")
        .setDescription("Документация API для лабораторных работ №2-№4")
        .setVersion("1.0")
        .addBearerAuth()
        .build();
      const document = SwaggerModule.createDocument(app, config);
      SwaggerModule.setup("api/docs", app, document);
    }
    ```

3.  Убедитесь, что при сборке Docker-образа для production (где `NODE_ENV=production`) маршрут `/api/docs` возвращает 404 Not Found.

### 3. Аннотирование Контроллеров и Маршрутов

Обновите все контроллеры, добавив мета-информацию:

- Теги (Tags): Сгруппируйте эндпоинты по модулям (например, "Auth", "Users", "Items").
- Описание операций: Краткое описание того, что делает метод.
- Статусы ответа: Явно укажите возможные коды состояния (200, 201, 400, 401, 403, 404, 500).
- Примеры (Examples): Для каждого DTO ответа добавьте пример данных. Это критически важно для понимания структуры фронтенд-разработчиками.

### 4. Документирование DTO и Моделей

Используйте декораторы или аннотации в классах DTO (Request/Response) для описания полей:

- Тип данных (string, number, boolean, array).
- Обязательность поля.
- Формат (email, date-time, uuid).
- Пример значения.
- Описание поля (что оно означает).

Убедитесь, что чувствительные поля (пароль, соль, хеш токена) не попадают в схему ответа Swagger, даже если они есть в entity. Используйте специальные декораторы исключения (например, `@ApiHideProperty()` в NestJS или `@JsonIgnore` в Spring).

### 5. Настройка схемы безопасности (Security Schemes)

Так как в лабораторной работе №3 реализована аутентификация через JWT в Cookies и OAuth, необходимо настроить Swagger UI для работы с ними:

1.  JWT / Cookie Auth: Настройте схему безопасности так, чтобы Swagger UI отправлял запросы с необходимыми заголовками или куками.
    - Если токены передаются в `HttpOnly` cookies, браузер отправит их автоматически при запросе из Swagger UI (если домены совпадают), но для явного указания в документации стоит добавить схему типа `apiKey` (в cookie) или `http` (bearer), объяснив в описании, что реальное приложение использует Cookies.
2.  OAuth 2.0 Flow: Опишите поток OAuth 2.0 в спецификации (Authorization Code Grant), указав URL авторизации и токен-эндпоинты провайдера (VK/Yandex), чтобы в документации была видна схема взаимодействия.

### 6. Проверка защищенных эндпоинтов

Протестируйте через Swagger UI:

- Выполните запрос `/auth/login`. Убедитесь, что куки установлены.
- Выполните запрос к защищенному ресурсу (например, `GET /items` или `GET /auth/whoami`).
- Убедитесь, что запрос проходит успешно (200 OK).
- Попробуйте выполнить запрос без авторизации — убедитесь, что Swagger корректно отображает ошибку 401.
- Проверьте, что эндпоинты помечены значком "замка" (lock icon), указывающим на необходимость авторизации.

## Критерии приемки
1. Репозиторий: Код загружен на GitHub/GitLab.
2. Документация: Файл `README.md` содержит:
    -   Краткое описание проекта.
    -   Пример файла переменных окружения (`.env.example`).
3.  Доступность: При запуске в режиме `development` документация доступна по пути `/api/docs` (или аналогичному). При переключении `NODE_ENV=production` документация недоступна (404).
4.  Автоматизация: Спецификация генерируется автоматически на основе кода. Отсутствуют ручные YAML/JSON файлы описания API.
5.  Полнота:
    - Все эндпоинты лабораторной работы №2 и №3 присутствуют.
    - Для всех эндпоинтов указаны методы, пути, теги.
    - Присутствуют примеры успешных ответов и ошибок.
6.  Безопасность в документации:
    - Чувствительные данные (пароли, соли, полные токены) не отображаются в схемах ответов.
    - Защищенные эндпоинты маркированы как требующие авторизации.
    - Реализована возможность тестирования защищенных эндпоинтов через интерфейс Swagger (ввод токена).
7.  Качество описания: Поля DTO имеют понятные описания и типы. Примеры валидны.
8.  Инфраструктура: Приложение запускается через `docker-compose up --build`.

## Контрольные вопросы

1.  Что такое спецификация OpenAPI и чем она отличается от Swagger UI?
2.  Какие существуют подходы к созданию документации: Code-First и Design-First? Какой из них использовался в этой работе и какие у него плюсы/минусы?
3.  Почему важно скрывать документацию API в "боевой" среде? Какие риски несет открытая документация?
4.  Как правильно документировать схемы безопасности (Authentication Schemes) в OpenAPI, если приложение использует HttpOnly Cookies?
5.  Зачем нужны примеры в документации API? Как они помогают потребителям API?
6.  Какие HTTP коды ответов обязательно должны быть описаны для CRUD операций?

## Рекомендуемая литература и документация

- OpenAPI Specification: [Official Documentation](https://swagger.io/specification/)
- Swagger Tools: [Swagger.io Tools](https://swagger.io/tools/)
- NestJS Swagger: [Docs](https://docs.nestjs.com/openapi/introduction)
- SpringDoc OpenAPI: [GitHub Repository](https://github.com/springdoc/springdoc-openapi)
- FastAPI Metadata: [Docs](https://fastapi.tiangolo.com/tutorial/metadata/)
- OWASP API Security Top 10: [OWASP API Security](https://owasp.org/www-project-api-security/) (Раздел о чрезмерном раскрытии данных через документацию).






Ниже приведены инструкции для создания коллекции запросов в Postman, полностью покрывающие сценарии из примера. Все шаги предполагают, что сервер использует **JWT-токены** (access + refresh), которые backend возвращает в теле ответа, а клиент передаёт в заголовке `Authorization: Bearer <токен>`.
---

### Предварительная настройка (Environment)

Создайте новое окружение (Environment) со следующими переменными и начальными значениями:

| Переменная       | Начальное значение      |
|------------------|-------------------------|
| `base_url`       | `http://localhost:8000` |
| `email`          | `test@example.com`      |
| `password`       | `SecurePass123!`        |
| `access_token`   | *(оставьте пустым)*     |
| `refresh_token`  | *(оставьте пустым)*     |

---

### 1. Регистрация (POST /auth/register)

**Method:** `POST`  
**URL:** `{{base_url}}/auth/register`  
**Headers:** `Content-Type: application/json`  
**Body (raw JSON):**
```json
{
  "email": "{{email}}",
  "password": "{{password}}",
  "first_name": "Test",
  "last_name": "User"
}
```
**Ожидаемый результат:** `201 Created`

---

### 2. Вход (POST /auth/login)

**Method:** `POST`  
**URL:** `{{base_url}}/auth/login`  
**Headers:** `Content-Type: application/json`  
**Body (raw JSON):**
```json
{
  "email": "{{email}}",
  "password": "{{password}}"
}
```
**Ожидаемый результат:** `200 OK`  
На вкладке **Tests** добавьте скрипт для автоматического сохранения токенов:
```javascript
if (pm.response.code === 200) {
    const json = pm.response.json();
    if (json.access_token) {
        pm.environment.set("access_token", json.access_token);
    }
    if (json.refresh_token) {
        pm.environment.set("refresh_token", json.refresh_token);
    }
}
```

---

### 3. Доступ к защищённому ресурсу без токена

**Method:** `GET`  
**URL:** `{{base_url}}/resources/`  
**Headers:** *без заголовка Authorization*  
**Ожидаемый результат:** `401 Unauthorized`

---

### 4. Доступ к защищённому ресурсу с токеном

**Method:** `GET`  
**URL:** `{{base_url}}/resources/`  
**Headers:** `Authorization: Bearer {{access_token}}`  
**Ожидаемый результат:** `200 OK`

---

### 5. Обновление токенов (Refresh)

**Method:** `POST`  
**URL:** `{{base_url}}/auth/refresh`  
**Headers:** `Content-Type: application/json`  
**Body (raw JSON):**
```json
{
  "refresh_token": "{{refresh_token}}"
}
```
**Ожидаемый результат:** `200 OK`  
На вкладке **Tests** обновите переменные новыми токенами:
```javascript
if (pm.response.code === 200) {
    const json = pm.response.json();
    if (json.access_token) {
        pm.environment.set("access_token", json.access_token);
    }
    if (json.refresh_token) {
        pm.environment.set("refresh_token", json.refresh_token);
    }
}
```

---

### 6. Завершение текущей сессии (Logout)

**Method:** `POST`  
**URL:** `{{base_url}}/auth/logout`  
**Headers:** `Authorization: Bearer {{access_token}}`  
**Body:** *отсутствует (или по требованию API – например, `refresh_token` в теле)*  
**Ожидаемый результат:** `200 OK`  
После успешного выполнения очистите токены в скрипте **Tests**:
```javascript
if (pm.response.code === 200) {
    pm.environment.unset("access_token");
    pm.environment.unset("refresh_token");
}
```

---

### 7. Завершение всех сессий (Logout All)

**Method:** `POST`  
**URL:** `{{base_url}}/auth/logout-all`  
**Headers:** `Authorization: Bearer {{access_token}}`  
**Body:** *по необходимости*  
**Ожидаемый результат:** `200 OK`  
Очистите переменные аналогично предыдущему шагу:
```javascript
if (pm.response.code === 200) {
    pm.environment.unset("access_token");
    pm.environment.unset("refresh_token");
}
```

---

### 8. Вход через OAuth (Yandex / VK)

**Method:** `GET`  
**URL:** `{{base_url}}/auth/oauth/yandex`  
**Headers:** *нет*  
**Ожидаемый результат:** `302 Found` (или `200 OK`, если редирект обрабатывается иначе)  
*При необходимости на вкладке Tests можно сохранить токены из ответа, если они возвращаются.*

---

### 9. Проверка `/whoami`

**До входа (без токена):**  
- **Method:** `GET`  
- **URL:** `{{base_url}}/auth/whoami`  
- **Headers:** *без Authorization*  
- **Ожидаемый результат:** `401 Unauthorized`

**После входа (с токеном):**  
- **Method:** `GET`  
- **URL:** `{{base_url}}/auth/whoami`  
- **Headers:** `Authorization: Bearer {{access_token}}`  
- **Ожидаемый результат:** `200 OK` (возвращает информацию о пользователе)

---

### 10. Проверка уникальности солей (опционально)

Этот шаг нельзя выполнить напрямую через API – для него потребуется доступ к базе данных. В примере использовался `docker exec`.  
Вы можете воспроизвести его в терминале или добавить в коллекцию запрос к БД, если настроен соответствующий прокси-сервер (не входит в стандартный функционал Postman).  
**Рекомендация:** после регистрации двух пользователей с одинаковым паролем выполните в терминале:
```bash
docker exec -it wp_labs_db psql -U postgres -d wp_labs_db -c \
"SELECT email, password_hash FROM users WHERE email IN ('test@example.com', 'test2@example.com');"
```
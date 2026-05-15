# Contacts REST API

Contacts REST API — це REST API застосунок для керування контактами користувача.
Проєкт реалізований на FastAPI та підтримує авторизацію, JWT токени, кешування через Redis, ролі користувачів, скидання пароля, тестування та документацію Sphinx.

## Основний функціонал

- Реєстрація користувача.
- Авторизація користувача.
- JWT авторизація з access та refresh токенами.
- Підтвердження email.
- Механізм скидання пароля.
- CRUD операції для контактів.
- Пошук контактів за іменем, прізвищем або email.
- Отримання контактів із днями народження протягом наступних 7 днів.
- Кешування поточного користувача через Redis.
- Ролі користувачів: `admin` та `user`.
- Обмеження доступу до окремих дій за ролями.
- Docker Compose для запуску застосунку.
- Unit та integration тести.
- Покриття тестами понад 75%.
- Документація Sphinx.

## Технології

- Python.
- FastAPI.
- SQLAlchemy.
- PostgreSQL.
- Redis.
- Docker.
- Docker Compose.
- JWT.
- Pytest.
- Pytest-cov.
- Sphinx.

## Запуск проєкту

Перед запуском потрібно створити файл `.env` на основі `.env.example` та заповнити необхідні змінні середовища.

Запуск застосунку:

```bash
docker-compose up --build -d
```

Після запуску API буде доступне за адресою:

```text
http://localhost:8000
```

Swagger документація:

```text
http://localhost:8000/docs
```

## Основні endpoints

### Authentication

```text
POST /api/auth/signup
POST /api/auth/login
GET /api/auth/confirmed_email/{token}
GET /api/auth/me
POST /api/auth/forgot_password
POST /api/auth/reset_password/{token}
PATCH /api/auth/avatar
```

### Contacts

```text
GET /api/contacts
POST /api/contacts
GET /api/contacts/{contact_id}
PATCH /api/contacts/{contact_id}
DELETE /api/contacts/{contact_id}
GET /api/contacts/search/
GET /api/contacts/birthdays
```

## JWT авторизація

У застосунку реалізована авторизація за допомогою JWT токенів.

Після успішного логіну користувач отримує:

```text
access_token
refresh_token
token_type
```

Access token використовується для доступу до захищених маршрутів.
Refresh token зберігається в базі даних для користувача.

## Redis кешування

Redis використовується для кешування поточного авторизованого користувача.

Ключ кешу має формат:

```text
user:{email}
```

Час життя кешу:

```text
900 секунд
```

Якщо користувач є в кеші, дані беруться з Redis.
Якщо користувача немає в кеші, він завантажується з бази даних і додається до кешу.

## Ролі користувачів

У проєкті реалізовано дві ролі:

```text
admin
user
```

Перевірка доступу реалізована через `RoleChecker`.

Приклад захищеного маршруту:

```text
PATCH /api/auth/avatar
```

Доступ до цього маршруту обмежується для користувачів з відповідною роллю.

## Скидання пароля

У застосунку реалізовано механізм скидання пароля.

Endpoints:

```text
POST /api/auth/forgot_password
POST /api/auth/reset_password/{token}
```

`forgot_password` створює token для скидання пароля.
`reset_password` перевіряє token та оновлює пароль користувача.

## Тестування

Запуск усіх тестів:

```bash
docker exec fastapi_app pytest --color=no
```

Очікуваний результат:

```text
23 passed
```

## Покриття тестами

Запуск тестів із перевіркою покриття:

```bash
docker exec fastapi_app pytest --cov=src --cov-report=term-missing --color=no
```

Поточний результат покриття:

```text
TOTAL 82%
```

Це більше ніж 75%, тому вимога щодо покриття тестами виконана.

## HTML coverage report

Для генерації HTML-звіту покриття:

```bash
docker exec fastapi_app pytest --cov=src --cov-report=html --color=no
```

Скопіювати HTML-звіт з контейнера:

```bash
docker cp fastapi_app:/app/htmlcov ./htmlcov
```

Відкрити файл:

```text
htmlcov/index.html
```

## Sphinx документація

Для генерації документації Sphinx:

```bash
docker exec fastapi_app sphinx-build -b html docs/ docs/_build/html
```

Скопіювати документацію з контейнера:

```powershell
Remove-Item -Recurse -Force docs_output
docker cp fastapi_app:/app/docs/_build/html ./docs_output
```

Відкрити файл:

```text
docs_output/index.html
```

Документація містить опис основних модулів, маршрутів, сервісів, репозиторіїв, моделей та схем.

## Структура проєкту

```text
src/
├── database/
│   ├── db.py
│   └── models.py
├── repository/
│   ├── contacts.py
│   └── users.py
├── routes/
│   ├── auth.py
│   ├── contacts.py
│   └── users.py
├── services/
│   ├── auth.py
│   ├── email.py
│   └── roles.py
└── schemas.py

tests/
├── conftest.py
├── test_route_auth.py
├── test_route_contacts.py
├── test_unit_repository_contacts.py
└── test_unit_repository_users.py

docs/
├── conf.py
└── index.rst
```

## Docker

Проєкт запускається через Docker Compose.

Основні сервіси:

```text
fastapi_app
postgres_db
redis_cache
```

Команда запуску:

```bash
docker-compose up --build -d
```

Команда зупинки:

```bash
docker-compose down
```

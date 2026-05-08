
**Це RESTful API для керування списком контактів, побудоване на FastAPI. Сервіс підтримує повний цикл CRUD для контактів, систему реєстрації та аутентифікації користувачів за допомогою JWT-токенів.**

- **Framework:** FastAPI
- **Database:** PostgreSQL + SQLAlchemy
- **Security:** JWT (JSON Web Tokens), Bcrypt hashing
- **Validation:** Pydantic (v2)
- **Environment:** Python-dotenv

- **Аутентифікація:** Реєстрація (201 Created) та логін з отриманням токена доступу.
- **Безпека:** Паролі зберігаються в хешованому вигляді (Passlib/Bcrypt).
- **CRUD:** Повний контроль над контактами (створення, читання, оновлення, видалення).
- **Розумний пошук:** Фільтрація за іменем, прізвищем або email.
- **Birthdays:** Окремий функціонал для отримання списку контактів, у яких день народження протягом наступних 7 днів.


1. **Клонуйте репозиторій:**
   ```bash
   git clone <your-repo-url>
   cd goit-pythonweb-hw-10

2. **Налаштуйте змінні оточення:**
Створіть файл .env на основі .env.example та вкажіть ваші дані для БД та секретний ключ.

3. **Встановіть залежності:**
    Bash
    pip install -r requirements.txt

4. **Запустіть сервер:**
   ```bash
   uvicorn main:app --reload

**Після запуску перейдіть за адресою:**
    http://127.0.0.1:8000/docs

**Там ви знайдете всі доступні ендпоінти та зможете протестувати запити в реальному часі.**

    Signup: POST /api/auth/signup (Тіло: email, password) -> Повертає 201 Created.
    Login: POST /api/auth/login (Тіло: username, password) -> Повертає Access Token.
    Get Birthdays: GET /api/contacts/birthdays -> Повертає список іменинників на найближчий тиждень.
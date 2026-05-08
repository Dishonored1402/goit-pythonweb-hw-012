from sqlalchemy.orm import Session
from src.database.models import User
from src.schemas import UserSchema

async def get_user_by_email(email: str, db: Session) -> User | None:
    return db.query(User).filter(User.email == email).first()

async def create_user(body: UserSchema, db: Session) -> User:
    avatar = None
    try:
        import hashlib
        g_hash = hashlib.md5(body.email.lower().encode()).hexdigest()
        avatar = f"https://www.gravatar.com/avatar/{g_hash}?d=identicon"
    except Exception:
        pass

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

async def update_token(user: User, token: str | None, db: Session) -> None:
    user.refresh_token = token
    db.commit()
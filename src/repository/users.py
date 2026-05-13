from sqlalchemy.orm import Session
from src.database.models import User, Role
from src.schemas import UserSchema
from libgravatar import Gravatar


async def get_user_by_email(email: str, db: Session):
    """Get a user by email address.

    :param email: User's email address.
    :param db: Database session.
    :return: User object or None.
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserSchema, db: Session):
    """Create a new user with Gravatar avatar.

    :param body: User registration data.
    :param db: Database session.
    :return: Newly created User object.
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(f"Gravatar error: {e}")

    new_user = User(**body.model_dump(), avatar=avatar, role=Role.user)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session):
    """Update user's refresh token.

    :param user: User object.
    :param token: New refresh token or None.
    :param db: Database session.
    """
    user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    """Mark user's email as confirmed.

    :param email: User's email address.
    :param db: Database session.
    """
    user = await get_user_by_email(email, db)
    if user:
        user.confirmed = True
        db.commit()


async def update_avatar(email: str, url: str, db: Session) -> User:
    """Update user's avatar URL.

    :param email: User's email address.
    :param url: New avatar URL.
    :param db: Database session.
    :return: Updated User object.
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user


async def update_password(user: User, password: str, db: Session) -> None:
    """Update user's hashed password.

    :param user: User object.
    :param password: New hashed password.
    :param db: Database session.
    """
    user.password = password
    db.commit()
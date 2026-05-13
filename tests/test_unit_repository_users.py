import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from src.database.models import User, Role
from src.schemas import UserSchema
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar,
    update_password
)

class TestUsers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, email="test@example.com", confirmed=False)

    async def test_get_user_by_email(self):
        self.session.query().filter().first.return_value = self.user
        result = await get_user_by_email(email="test@example.com", db=self.session)
        self.assertEqual(result, self.user)

    async def test_create_user(self):
        body = UserSchema(username="tester", email="tester@example.com", password="password")
        result = await create_user(body=body, db=self.session)
        self.assertEqual(result.email, body.email)
        self.session.commit.assert_called_once()

    async def test_update_token(self):
        await update_token(user=self.user, token="new_token", db=self.session)
        self.assertEqual(self.user.refresh_token, "new_token")
        self.session.commit.assert_called_once()

    async def test_confirmed_email(self):
        self.session.query().filter().first.return_value = self.user
        await confirmed_email(email="test@example.com", db=self.session)
        self.assertTrue(self.user.confirmed)
        self.session.commit.assert_called_once()

    async def test_update_avatar(self):
        self.session.query().filter().first.return_value = self.user
        result = await update_avatar(email="test@example.com", url="http://image.com", db=self.session)
        self.assertEqual(result.avatar, "http://image.com")

    async def test_update_password(self):
        await update_password(user=self.user, password="new_hashed_password", db=self.session)
        self.assertEqual(self.user.password, "new_hashed_password")
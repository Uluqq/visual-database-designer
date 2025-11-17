# controllers/user_controller.py

from models.base import SessionLocal
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session


class UserController:

    def register_user(self, username, email, password) -> (User | None, str):
        session = SessionLocal()
        try:
            if session.query(User).filter_by(username=username).first():
                return None, "Пользователь с таким именем уже существует."
            if session.query(User).filter_by(email=email).first():
                return None, "Пользователь с таким email уже существует."
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, hash_password=hashed_password)

            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user, "Пользователь успешно зарегистрирован."
        except Exception as e:
            session.rollback()
            return None, f"Ошибка при регистрации: {e}"
        finally:
            session.close()

    def authenticate_user(self, username_or_email, password) -> User | None:
        session = SessionLocal()
        try:
            user = session.query(User).filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()

            if user and check_password_hash(user.hash_password, password):
                return user
            return None
        finally:
            session.close()
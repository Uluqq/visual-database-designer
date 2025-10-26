# controllers/user_controller.py

from werkzeug.security import generate_password_hash, check_password_hash


# --- ВРЕМЕННАЯ ЗАГЛУШКА ВМЕСТО МОДЕЛИ SQLAlchemy ---
# Этот класс имитирует объект пользователя, который в будущем будет приходить из БД.
class User:
    def __init__(self, username, email, hash_password):
        self.username = username
        self.email = email
        self.hash_password = hash_password


class UserController:
    def __init__(self):
        # --- ВРЕМЕННАЯ БАЗА ДАННЫХ В ПАМЯТИ ---
        # Вместо подключения к БД, используем обычный словарь.
        # Все данные будут теряться при перезапуске приложения.
        self._users = {}
        self._add_test_user()  # Добавим тестового пользователя для удобства

    def _add_test_user(self):
        """Создает одного тестового пользователя при запуске."""
        test_username = "user"
        test_email = "user@example.com"
        test_password = "123"
        hashed_password = generate_password_hash(test_password)
        self._users[test_username] = {
            "email": test_email,
            "hash": hashed_password
        }
        print(f"--- Создан тестовый пользователь: login='{test_username}', password='{test_password}' ---")

    def register_user(self, username, email, password) -> (User | None, str):
        """Регистрирует нового пользователя в словаре."""
        if username in self._users:
            return None, "Пользователь с таким именем уже существует."

        # Проверим, не занят ли email
        for u_data in self._users.values():
            if u_data['email'] == email:
                return None, "Пользователь с таким email уже существует."

        hashed_password = generate_password_hash(password)
        self._users[username] = {
            "email": email,
            "hash": hashed_password
        }

        # Возвращаем "фальшивый" объект User и сообщение
        new_user_obj = User(username=username, email=email, hash_password=hashed_password)
        return new_user_obj, "Пользователь успешно зарегистрирован."

    def authenticate_user(self, username_or_email, password) -> User | None:
        """Аутентифицирует пользователя по данным из словаря."""
        user_data = None
        found_username = None

        # Сначала ищем по имени пользователя
        if username_or_email in self._users:
            user_data = self._users[username_or_email]
            found_username = username_or_email
        else:
            # Если не нашли, ищем по email
            for uname, u_data in self._users.items():
                if u_data['email'] == username_or_email:
                    user_data = u_data
                    found_username = uname
                    break

        if user_data and check_password_hash(user_data['hash'], password):
            # Возвращаем "фальшивый" объект User
            return User(username=found_username, email=user_data['email'], hash_password=user_data['hash'])

        return None
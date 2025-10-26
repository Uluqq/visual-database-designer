# controllers/project_controller.py

# --- ВРЕМЕННАЯ ЗАГЛУШКА ВМЕСТО МОДЕЛИ SQLAlchemy ---
# Этот класс имитирует объект проекта, который в будущем будет приходить из БД.
class Project:
    def __init__(self, project_id, project_name, description, user_id):
        self.project_id = project_id
        self.project_name = project_name
        self.description = description
        self.user_id = user_id


class ProjectController:
    def __init__(self):
        # --- ВРЕМЕННАЯ БАЗА ДАННЫХ В ПАМЯТИ ---
        # Ключ - user_id, значение - список его проектов
        self._projects = {}
        self._next_project_id = 1
        self._add_test_projects()

    def _add_test_projects(self):
        """Создает пару тестовых проектов для пользователя 'user'."""
        # Мы знаем, что в UserController есть тестовый 'user',
        # поэтому создадим проекты для него. В реальном приложении
        # user_id будет приходить от реального объекта пользователя.
        test_user_id = 1  # Условно присвоим ID=1 нашему 'user'

        self.create_project(
            user_id=test_user_id,
            project_name="E-commerce Analytics",
            description="Schema for our online store."
        )
        self.create_project(
            user_id=test_user_id,
            project_name="Blog Platform",
            description="Database structure for a multi-user blog."
        )
        print("--- Созданы тестовые проекты ---")

    def get_projects_for_user(self, user_id: int) -> list[Project]:
        """Возвращает список проектов для указанного ID пользователя."""
        return self._projects.get(user_id, [])

    def create_project(self, user_id: int, project_name: str, description: str = "") -> Project:
        """Создает новый проект для пользователя и возвращает его."""
        if user_id not in self._projects:
            self._projects[user_id] = []

        new_project = Project(
            project_id=self._next_project_id,
            project_name=project_name,
            description=description,
            user_id=user_id
        )

        self._projects[user_id].append(new_project)
        self._next_project_id += 1

        return new_project
# controllers/project_controller.py

from models.base import SessionLocal
from models.project import Project, Schema  # <-- Импортируем Schema


class ProjectController:

    def get_projects_for_user(self, user_id: int) -> list[Project]:
        """Возвращает список проектов для указанного ID пользователя из БД."""
        session = SessionLocal()
        try:
            projects = session.query(Project).filter(Project.user_id == user_id).all()
            return projects
        finally:
            session.close()

    def create_project(self, user_id: int, project_name: str, description: str = "") -> Project:
        """
        Создает новый проект для пользователя в БД, а также
        автоматически создает для него схему по умолчанию.
        """
        session = SessionLocal()
        try:
            # 1. Создаем объект проекта
            new_project = Project(
                project_name=project_name,
                description=description,
                user_id=user_id
            )

            # 2. Создаем для него схему по умолчанию и добавляем к проекту
            # SQLAlchemy сам разберется с project_id после коммита
            default_schema = Schema(schema_name="public")
            new_project.schemas.append(default_schema)

            # 3. Сохраняем все в БД
            session.add(new_project)
            session.commit()
            session.refresh(new_project)
            return new_project
        except Exception as e:
            session.rollback()
            print(f"Ошибка при создании проекта: {e}")
            return None
        finally:
            session.close()
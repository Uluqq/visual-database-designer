# controllers/project_controller.py

from models.base import SessionLocal
from models.project import Project # <-- Импортируем настоящую модель Project

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
        """Создает новый проект для пользователя в БД и возвращает его."""
        session = SessionLocal()
        try:
            new_project = Project(
                project_name=project_name,
                description=description,
                user_id=user_id
            )
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
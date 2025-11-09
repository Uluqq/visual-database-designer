# controllers/project_controller.py

from models.base import SessionLocal
from models.project import Project, Schema
from models.table import Table, TableColumn
from models.relationships import Relationship, RelationshipColumn
from models.user import Connection
from sqlalchemy import desc
from utils.schema_inspector import inspect_mysql_database
from .diagram_controller import DiagramController


class ProjectController:
    def get_projects_for_user(self, user_id: int) -> list[Project]:
        session = SessionLocal()
        try:
            return session.query(Project).filter(Project.user_id == user_id).order_by(desc(Project.updated_at)).all()
        finally:
            session.close()

    def create_project(self, user_id: int, project_name: str, description: str = "") -> Project:
        session = SessionLocal()
        try:
            new_project = Project(project_name=project_name, description=description, user_id=user_id)
            new_project.schemas.append(Schema(schema_name="public"))
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

    def import_project_from_db(self, user_id: int, connection: Connection, db_name: str) -> (Project | None, str):
        schema_data, error = inspect_mysql_database(connection, db_name)
        if error:
            return None, error

        session = SessionLocal()
        try:
            # 1. Создание проекта, схемы и диаграммы
            project_name = f"Импорт MySQL: {db_name}"
            new_project = Project(project_name=project_name, user_id=user_id)
            new_schema = Schema(schema_name="public")
            new_project.schemas.append(new_schema)
            session.add(new_project)

            # --- VVV --- ИЗМЕНЕНИЕ: Используем commit() вместо flush() --- VVV ---
            # Коммитим создание проекта. Это завершает транзакцию и гарантирует,
            # что project_id будет доступен в любой новой сессии.
            session.commit()
            session.refresh(new_project)
            # --- ^^^ --- КОНЕЦ ИЗМЕНЕНИЯ --- ^^^ ---

            diagram_ctrl = DiagramController()
            # Этот метод теперь будет работать в своей собственной, новой транзакции,
            # но он найдет проект, так как он уже закоммичен.
            main_diagram = diagram_ctrl.get_or_create_diagram_for_project(new_project.project_id)

            created_tables = {}
            created_columns = {}

            # 2. Создание таблиц и колонок
            for table_info in schema_data['tables']:
                new_table = Table(table_name=table_info['name'], schema_id=new_schema.schema_id)
                session.add(new_table)  # Добавляем каждую таблицу в сессию
                created_tables[table_info['name']] = new_table
                for col_info in table_info['columns']:
                    new_col = TableColumn(
                        column_name=col_info['name'], data_type=col_info['type'],
                        is_primary_key=col_info['is_pk'], is_nullable=col_info['nullable'])
                    new_table.columns.append(new_col)
                    created_columns[f"{table_info['name']}.{col_info['name']}"] = new_col

            # --- VVV --- ИЗМЕНЕНИЕ: Снова используем commit() --- VVV ---
            # Коммитим создание всех таблиц и колонок.
            # После этого у всех объектов Table в created_tables будут ID.
            session.commit()
            # --- ^^^ --- КОНЕЦ ИЗМЕНЕНИЯ --- ^^^ ---

            # 3. Создание DiagramObjects
            x, y, col_count = 50, 50, 0
            for table_name, table_obj in created_tables.items():
                # Этот метод будет работать в своей собственной транзакции
                diagram_ctrl.add_existing_table_to_diagram(
                    main_diagram.diagram_id, table_obj.table_id, x, y
                )
                x += 350
                col_count += 1
                if col_count % 4 == 0:
                    x = 50
                    y += 250

            # 4. Создание связей
            for table_info in schema_data['tables']:
                for fk_info in table_info['foreign_keys']:
                    start_table = created_tables.get(fk_info['target_table'])
                    end_table = created_tables.get(fk_info['source_table'])
                    if not start_table or not end_table: continue

                    start_col = created_columns.get(f"{fk_info['target_table']}.{fk_info['target_column']}")
                    end_col = created_columns.get(f"{fk_info['source_table']}.{fk_info['source_column']}")
                    if not start_col or not end_col: continue

                    # Обновляем объекты, чтобы получить их ID из БД
                    session.refresh(start_col)
                    session.refresh(end_col)

                    new_rel = Relationship(
                        project_id=new_project.project_id, start_table_id=start_table.table_id,
                        end_table_id=end_table.table_id, constraint_name=fk_info.get('CONSTRAINT_NAME'))
                    new_rel.relationship_columns.append(
                        RelationshipColumn(start_column_id=start_col.column_id, end_column_id=end_col.column_id))
                    session.add(new_rel)

            session.commit()  # Финальный коммит для связей
            return new_project, "Проект успешно импортирован!"
        except Exception as e:
            session.rollback()
            import traceback
            traceback.print_exc()
            return None, f"Ошибка во время импорта: {e}"
        finally:
            session.close()
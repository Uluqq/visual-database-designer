# controllers/project_controller.py

from models.base import SessionLocal
from models.project import Project, Schema
from models.table import Table, TableColumn
from models.relationships import Relationship, RelationshipColumn
from models.user import Connection
from sqlalchemy import desc
# --- ИЗМЕНЕНИЕ: Импортируем правильный инспектор ---
from utils.schema_inspector import inspect_mysql_database

class ProjectController:
    # ... (get_projects_for_user и create_project без изменений)
    def get_projects_for_user(self, user_id: int) -> list[Project]:
        session = SessionLocal()
        try: return session.query(Project).filter(Project.user_id == user_id).order_by(desc(Project.updated_at)).all()
        finally: session.close()
    def create_project(self, user_id: int, project_name: str, description: str = "") -> Project:
        session = SessionLocal();
        try:
            new_project = Project(project_name=project_name, description=description, user_id=user_id)
            new_project.schemas.append(Schema(schema_name="public"))
            session.add(new_project); session.commit(); session.refresh(new_project)
            return new_project
        except Exception as e:
            session.rollback(); print(f"Ошибка: {e}"); return None
        finally: session.close()

    # --- ИЗМЕНЕНИЕ: Сигнатура и логика метода импорта ---
    def import_project_from_db(self, user_id: int, connection: Connection, db_name: str) -> (Project | None, str):
        schema_data, error = inspect_mysql_database(connection, db_name)
        if error:
            return None, error
        session = SessionLocal()
        try:
            project_name = f"Импорт MySQL: {db_name}"
            new_project = Project(project_name=project_name, user_id=user_id)
            new_project.schemas.append(Schema(schema_name="public"))
            created_tables = {}; created_columns = {}
            for table_info in schema_data['tables']:
                new_table = Table(table_name=table_info['name'], schema=new_project.schemas[0])
                created_tables[table_info['name']] = new_table
                for col_info in table_info['columns']:
                    new_col = TableColumn(
                        column_name=col_info['name'], data_type=col_info['type'],
                        is_primary_key=col_info['is_pk'], is_nullable=col_info['nullable']
                    )
                    new_table.columns.append(new_col)
                    created_columns[f"{table_info['name']}.{col_info['name']}"] = new_col
            session.add(new_project); session.flush()
            for table_info in schema_data['tables']:
                for fk_info in table_info['foreign_keys']:
                    start_table = created_tables.get(fk_info['target_table'])
                    end_table = created_tables.get(fk_info['source_table'])
                    if not start_table or not end_table: continue
                    start_col = created_columns.get(f"{fk_info['target_table']}.{fk_info['target_column']}")
                    end_col = created_columns.get(f"{fk_info['source_table']}.{fk_info['source_column']}")
                    if not start_col or not end_col: continue
                    new_rel = Relationship(
                        project_id=new_project.project_id, start_table_id=start_table.table_id,
                        end_table_id=end_table.table_id, constraint_name=fk_info.get('CONSTRAINT_NAME')
                    )
                    new_rel.relationship_columns.append(RelationshipColumn(start_column_id=start_col.column_id, end_column_id=end_col.column_id))
                    session.add(new_rel)
            session.commit(); return new_project, "Проект успешно импортирован!"
        except Exception as e:
            session.rollback(); return None, f"Ошибка во время импорта: {e}"
        finally: session.close()
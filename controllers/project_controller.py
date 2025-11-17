# controllers/project_controller.py

from models.base import SessionLocal
from models.project import Project, Schema
from models.table import Table, TableColumn, DbIndex, IndexColumn
from models.relationships import Relationship, RelationshipColumn
from models.user import Connection
from sqlalchemy import desc, select
from sqlalchemy.orm import joinedload, selectinload
from utils.schema_inspector import inspect_mysql_database
from .diagram_controller import DiagramController


class ProjectController:
    def get_all_tables_for_project(self, project_id: int) -> list[Table]:
        """
        Возвращает список ВСЕХ таблиц проекта, сразу "жадно" подгружая
        все необходимые для экспорта связанные данные (колонки, индексы).
        """
        session = SessionLocal()
        try:
            schema_id = session.execute(
                select(Schema.schema_id).filter_by(project_id=project_id)
            ).scalar_one_or_none()

            if not schema_id:
                return []

            # --- VVV --- ИЗМЕНЕНИЕ: Добавляем опции для жадной загрузки --- VVV ---
            return session.query(Table).filter_by(schema_id=schema_id).options(
                selectinload(Table.columns),
                selectinload(Table.indexes).selectinload(DbIndex.index_columns).joinedload(IndexColumn.column)
            ).order_by(Table.table_name).all()
            # --- ^^^ --- КОНЕЦ ИЗМЕНЕНИЯ --- ^^^ ---
        finally:
            session.close()

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
            session.add(new_project);
            session.commit();
            session.refresh(new_project)
            return new_project
        except Exception as e:
            session.rollback();
            return None
        finally:
            session.close()

    def import_project_from_db(self, user_id: int, connection: Connection, db_name: str) -> (Project | None, str):
        schema_data, error = inspect_mysql_database(connection, db_name)
        if error: return None, error
        session = SessionLocal()
        try:
            project_name = f"Импорт MySQL: {db_name}"
            new_project = Project(project_name=project_name, user_id=user_id)
            new_schema = Schema(schema_name="public")
            new_project.schemas.append(new_schema)
            session.add(new_project);
            session.commit();
            session.refresh(new_project)

            diagram_ctrl = DiagramController()
            main_diagram = diagram_ctrl.get_or_create_diagram_for_project(new_project.project_id)

            created_tables = {};
            created_columns = {}
            for table_info in schema_data['tables']:
                new_table = Table(table_name=table_info['name'], schema_id=new_schema.schema_id)
                session.add(new_table);
                created_tables[table_info['name']] = new_table
                for col_info in table_info['columns']:
                    new_col = TableColumn(
                        column_name=col_info['name'], data_type=col_info['type'],
                        is_primary_key=col_info['is_pk'], is_nullable=col_info['nullable'])
                    new_table.columns.append(new_col)
                    created_columns[f"{table_info['name']}.{col_info['name']}"] = new_col
            session.commit()

            x, y, col_count = 50, 50, 0
            for table_name, table_obj in created_tables.items():
                diagram_ctrl.add_existing_table_to_diagram(main_diagram.diagram_id, table_obj.table_id, x, y)
                x += 350;
                col_count += 1
                if col_count % 4 == 0: x = 50; y += 250

            for table_info in schema_data['tables']:
                for fk_info in table_info['foreign_keys']:
                    start_table = created_tables.get(fk_info['target_table'])
                    end_table = created_tables.get(fk_info['source_table'])
                    if not start_table or not end_table: continue
                    start_col = created_columns.get(f"{fk_info['target_table']}.{fk_info['target_column']}")
                    end_col = created_columns.get(f"{fk_info['source_table']}.{fk_info['source_column']}")
                    if not start_col or not end_col: continue
                    session.refresh(start_col);
                    session.refresh(end_col)
                    new_rel = Relationship(
                        project_id=new_project.project_id, start_table_id=start_table.table_id,
                        end_table_id=end_table.table_id, constraint_name=fk_info.get('CONSTRAINT_NAME'))
                    new_rel.relationship_columns.append(
                        RelationshipColumn(start_column_id=start_col.column_id, end_column_id=end_col.column_id))
                    session.add(new_rel)
            session.commit()
            return new_project, "Проект успешно импортирован!"
        except Exception as e:
            session.rollback();
            import traceback;
            traceback.print_exc();
            return None, f"Ошибка во время импорта: {e}"
        finally:
            session.close()
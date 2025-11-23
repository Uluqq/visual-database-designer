# utils/validator.py

from models.project import Project
from models.table import Table
from models.relationships import Relationship
from controllers.project_controller import ProjectController
from controllers.diagram_controller import DiagramController


class ProjectValidator:
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.project_ctrl = ProjectController()
        self.diagram_ctrl = DiagramController()
        self.errors = []
        self.warnings = []

    def validate(self) -> bool:
        """
        Запускает все проверки. Возвращает True, если критических ошибок нет.
        """
        self.errors.clear()
        self.warnings.clear()

        tables = self.project_ctrl.get_all_tables_for_project(self.project_id)
        relationships = self.diagram_ctrl.get_relationships_for_project(self.project_id)

        # Проверка 1: Таблицы
        table_names = set()
        for table in tables:
            # 1.1 Пустое имя таблицы
            if not table.table_name or not table.table_name.strip():
                self.errors.append(f"Таблица ID {table.table_id} не имеет имени.")
                continue

            # 1.2 Дубликаты имен таблиц
            if table.table_name in table_names:
                self.errors.append(f"Дублирующееся имя таблицы: '{table.table_name}'.")
            table_names.add(table.table_name)

            # 1.3 Таблица без колонок
            if not table.columns:
                self.errors.append(f"Таблица '{table.table_name}' не содержит колонок.")

            # 1.4 Проверки внутри таблицы (Колонки)
            col_names = set()
            has_pk = False
            for col in table.columns:
                if not col.column_name.strip():
                    self.errors.append(f"В таблице '{table.table_name}' есть колонка без имени.")

                if col.column_name in col_names:
                    self.errors.append(f"В таблице '{table.table_name}' дублируется колонка '{col.column_name}'.")
                col_names.add(col.column_name)

                if col.is_primary_key:
                    has_pk = True

                    # --- НОВАЯ ПРОВЕРКА: PK + Default Value ---
                    if col.default_value and col.default_value.strip():
                        # Если значение не похоже на функцию (нет скобок), это подозрительно
                        if "(" not in col.default_value:
                            self.warnings.append(
                                f"Таблица '{table.table_name}': Колонка '{col.column_name}' является Primary Key, "
                                f"но имеет статическое значение по умолчанию '{col.default_value}'. "
                                f"Это приведет к ошибке уникальности при вставке второй записи."
                            )
                        else:
                            # Если есть скобки, например "UUID()", это может быть ок, но все равно предупредим аккуратно
                            pass

                            # 2.1 Warning: Нет PK
            if not has_pk:
                self.warnings.append(f"Таблица '{table.table_name}' не имеет Первичного Ключа (PK).")

            # 1.5 Индексы
            for idx in table.indexes:
                if not idx.index_columns:
                    self.errors.append(f"Индекс '{idx.index_name}' в таблице '{table.table_name}' пуст.")

        # Проверка 3: Связи (Foreign Keys)
        for rel in relationships:
            if not rel.relationship_columns:
                continue

            rel_col = rel.relationship_columns[0]
            start_col = rel_col.start_column  # Parent (на кого ссылаются)
            end_col = rel_col.end_column  # Child (кто ссылается, FK)

            start_table = start_col.table
            end_table = end_col.table

            # 3.1 Проверка совпадения типов данных
            if start_col.data_type.lower() != end_col.data_type.lower():
                self.errors.append(
                    f"Ошибка связи '{end_table.table_name}' -> '{start_table.table_name}': "
                    f"Типы данных не совпадают! "
                    f"({end_col.column_name}: {end_col.data_type} != {start_col.column_name}: {start_col.data_type})"
                )

            # 3.2 Целевая колонка должна быть уникальной (PK или Unique)
            is_target_valid = start_col.is_primary_key or start_col.is_unique

            if not is_target_valid:
                for idx in start_table.indexes:
                    if idx.is_unique and len(idx.index_columns) == 1 and idx.index_columns[
                        0].column_id == start_col.column_id:
                        is_target_valid = True
                        break

            if not is_target_valid:
                self.errors.append(
                    f"Ошибка связи: Колонка '{start_table.table_name}.{start_col.column_name}' "
                    f"должна быть PRIMARY KEY или UNIQUE, чтобы на нее можно было ссылаться."
                )

        return len(self.errors) == 0
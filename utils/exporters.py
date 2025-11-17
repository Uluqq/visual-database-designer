# utils/exporters.py

from models.project import Project
from models.table import Table, TableColumn, DbIndex
from models.relationships import Relationship


class MySqlExporter:
    """
    Генерирует DDL-скрипт для MySQL на основе моделей проекта.
    """

    def __init__(self, tables: list[Table], relationships: list[Relationship]):
        self.tables = tables
        self.relationships = relationships
        self.sql_script = ""

    def generate_script(self) -> str:
        """Основной метод, генерирующий полный SQL-скрипт."""
        create_tables_sql = self._generate_create_tables()
        add_constraints_sql = self._generate_foreign_keys()

        self.sql_script = "-- Сгенерировано Visual Database Designer\n\n"
        self.sql_script += create_tables_sql
        self.sql_script += "\n\n-- Внешние ключи\n"
        self.sql_script += add_constraints_sql

        return self.sql_script

    def _generate_create_tables(self) -> str:
        statements = []
        for table in self.tables:
            columns_sql = []
            primary_keys = []

            sorted_columns = sorted(table.columns, key=lambda c: c.column_id)

            for col in sorted_columns:
                col_def = f"  `{col.column_name}` {self._map_type(col.data_type)}"

                if not col.is_nullable:
                    col_def += " NOT NULL"
                else:
                    col_def += " NULL"

                if col.is_primary_key:
                    primary_keys.append(f"`{col.column_name}`")

                if col.is_unique and not col.is_primary_key:
                    col_def += " UNIQUE"

                default_val = col.default_value
                if default_val is not None:
                    if default_val.isnumeric():
                        col_def += f" DEFAULT {default_val}"
                    else:
                        escaped_val = default_val.replace("'", "''")
                        col_def += f" DEFAULT '{escaped_val}'"

                columns_sql.append(col_def)

            if primary_keys:
                columns_sql.append(f"  PRIMARY KEY ({', '.join(primary_keys)})")

            for index in table.indexes:
                if not index.is_primary_key:
                    idx_type = "UNIQUE INDEX" if index.is_unique else "INDEX"
                    sorted_idx_cols = sorted(index.index_columns, key=lambda ic: ic.order)
                    idx_col_names = ", ".join([f"`{ic.column.column_name}`" for ic in sorted_idx_cols])
                    columns_sql.append(f"  {idx_type} `{index.index_name}` ({idx_col_names})")

            table_sql = f"CREATE TABLE `{table.table_name}` (\n"
            table_sql += ",\n".join(columns_sql)
            table_sql += "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n"
            statements.append(table_sql)

        return "\n".join(statements)

    def _generate_foreign_keys(self) -> str:
        statements = []
        for rel in self.relationships:
            if not rel.relationship_columns:
                continue

            rel_col = rel.relationship_columns[0]

            start_table = rel_col.start_column.table
            end_table = rel_col.end_column.table

            target_column = rel_col.start_column
            if not target_column.is_primary_key and not target_column.is_unique:
                statements.append(
                    f"-- ПРЕДУПРЕЖДЕНИЕ: Невозможно создать FK, так как целевая колонка `{start_table.table_name}`.`{target_column.column_name}` не является UNIQUE или PRIMARY KEY.\n"
                    f"-- ALTER TABLE `{end_table.table_name}` ADD CONSTRAINT `fk_{end_table.table_name}_{start_table.table_name}` FOREIGN KEY (`{rel_col.end_column.column_name}`) REFERENCES `{start_table.table_name}` (`{target_column.column_name}`);\n"
                )
                continue

            constraint_name = rel.constraint_name or f"fk_{end_table.table_name}_{start_table.table_name}"

            sql = (
                f"ALTER TABLE `{end_table.table_name}` "
                f"ADD CONSTRAINT `{constraint_name}` "
                f"FOREIGN KEY (`{rel_col.end_column.column_name}`) "
                f"REFERENCES `{start_table.table_name}` (`{target_column.column_name}`);"
            )
            statements.append(sql)

        return "\n".join(statements)

    def _map_type(self, internal_type: str) -> str:
        if 'varchar' in internal_type:
            return "VARCHAR(255)"
        if 'integer' in internal_type:
            return "INT"
        if 'timestamp' in internal_type:
            return "DATETIME"
        return internal_type.upper()
import pymysql
from typing import List, Dict, Any


class SchemaInspector:
    def __init__(self, host: str, port: int, user: str, password: str, db_name: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.connection = None

    def _connect(self):
        """Устанавливает соединение с конкретной базой данных."""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db_name,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5
            )
        except pymysql.err.OperationalError as e:
            raise Exception(f"Ошибка подключения к БД '{self.db_name}': {e}")

    def inspect_schema(self) -> Dict[str, Any]:
        """Извлекает структуру БД: таблицы, колонки и внешние ключи."""
        self._connect()
        if not self.connection:
            return {}

        try:
            tables = self._fetch_tables()
            columns = self._fetch_columns()
            foreign_keys = self._fetch_foreign_keys()

            # 🔹 Проставляем флаг is_fk для колонок, участвующих во внешних ключах
            for fk in foreign_keys:
                src_table = fk['source_table']
                src_column = fk['source_column']
                if src_table in columns:
                    for col in columns[src_table]:
                        if col['name'] == src_column:
                            col['is_fk'] = True

            schema_data = {
                'tables': tables,
                'columns': columns,
                'foreign_keys': foreign_keys
            }
            return schema_data

        finally:
            if self.connection:
                self.connection.close()

    def _fetch_tables(self) -> List[str]:
        """Получает список всех таблиц в текущей БД."""
        with self.connection.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            table_key = list(cursor.fetchone().keys())[0] if cursor.rowcount > 0 else None
            if table_key:
                cursor.scroll(0)
                return [row[table_key] for row in cursor.fetchall()]
            return []

    def _fetch_columns(self) -> Dict[str, List[Dict]]:
        """Получает колонки для всех таблиц."""
        columns_data = {}
        with self.connection.cursor() as cursor:
            sql = """
            SELECT 
                TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
            FROM 
                information_schema.COLUMNS 
            WHERE 
                TABLE_SCHEMA = %s 
            ORDER BY 
                TABLE_NAME, ORDINAL_POSITION;
            """
            cursor.execute(sql, (self.db_name,))

            for row in cursor.fetchall():
                table_name = row['TABLE_NAME']
                col_info = {
                    'name': row['COLUMN_NAME'],
                    'type': row['DATA_TYPE'],
                    'nullable': row['IS_NULLABLE'] == 'YES',
                    'not_null': row['IS_NULLABLE'] == 'NO',
                    'is_pk': row['COLUMN_KEY'] == 'PRI',
                    'is_fk': False
                }
                if table_name not in columns_data:
                    columns_data[table_name] = []
                columns_data[table_name].append(col_info)
        return columns_data

    def _fetch_foreign_keys(self) -> List[Dict]:
        """Получает информацию о внешних ключах."""
        fk_data = []
        with self.connection.cursor() as cursor:
            sql = """
            SELECT 
                kcu.CONSTRAINT_NAME,
                kcu.TABLE_NAME AS source_table,
                kcu.COLUMN_NAME AS source_column,
                kcu.REFERENCED_TABLE_NAME AS target_table,
                kcu.REFERENCED_COLUMN_NAME AS target_column
            FROM 
                information_schema.KEY_COLUMN_USAGE AS kcu
            WHERE 
                kcu.TABLE_SCHEMA = %s AND 
                kcu.REFERENCED_TABLE_NAME IS NOT NULL;
            """
            cursor.execute(sql, (self.db_name,))
            fk_data = cursor.fetchall()
        return fk_data

# utils/schema_inspector.py

import pymysql
from typing import List, Dict, Any
from models.user import Connection

def list_databases_on_server(connection_obj: Connection) -> (List[str] | None, str | None):
    """Подключается к серверу MySQL и возвращает список баз данных."""
    try:
        password = connection_obj.db_password_hash
        conn = pymysql.connect(
            host=connection_obj.host, port=connection_obj.port,
            user=connection_obj.db_username, password=password,
            cursorclass=pymysql.cursors.DictCursor, connect_timeout=5
        )
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES;")
            # Исключаем системные базы данных из списка
            system_dbs = ['information_schema', 'mysql', 'performance_schema', 'sys']
            databases = [row['Database'] for row in cursor.fetchall() if row['Database'] not in system_dbs]
            return databases, None
    except Exception as e:
        return None, f"Не удалось получить список БД: {e}"

def inspect_mysql_database(connection_obj: Connection, db_name: str) -> (dict | None, str | None):
    """Принимает объект Connection и ИМЯ БД, создает инспектор и возвращает структуру."""
    try:
        password = connection_obj.db_password_hash
        inspector = SchemaInspector(
            host=connection_obj.host, port=connection_obj.port, user=connection_obj.db_username,
            password=password, db_name=db_name
        )
        raw_data = inspector.inspect_schema()
        schema_data = {'tables': []}
        for table_name in raw_data.get('tables', []):
            table_info = {
                'name': table_name,
                'columns': raw_data.get('columns', {}).get(table_name, []),
                'foreign_keys': [fk for fk in raw_data.get('foreign_keys', []) if fk.get('source_table') == table_name]
            }
            primary_keys = [col['name'] for col in table_info['columns'] if col.get('is_pk')]
            table_info['primary_key'] = primary_keys
            schema_data['tables'].append(table_info)
        return schema_data, None
    except Exception as e:
        return None, str(e)

def test_mysql_connection(data: dict) -> (bool, str):
    """Проверяет, можно ли установить соединение с СЕРВЕРОМ MySQL (без выбора БД)."""
    try:
        pymysql.connect(
            host=data['host'], port=data['port'], user=data['user'],
            password=data['password'], connect_timeout=5
        )
        return True, "Соединение с сервером успешно установлено!"
    except pymysql.err.OperationalError as e:
        return False, f"Ошибка подключения: Неверные данные или сервер недоступен.\n({e})"
    except Exception as e:
        return False, f"Произошла непредвиденная ошибка: {e}"


class SchemaInspector:
    # ... (Этот класс остается без изменений, как в вашем файле)
    def __init__(self, host: str, port: int, user: str, password: str, db_name: str):
        self.host = host; self.port = port; self.user = user; self.password = password;
        self.db_name = db_name; self.connection = None
    def _connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host, port=self.port, user=self.user, password=self.password,
                database=self.db_name, cursorclass=pymysql.cursors.DictCursor, connect_timeout=5)
        except pymysql.err.OperationalError as e:
            raise Exception(f"Ошибка подключения к БД '{self.db_name}': {e}")
    def inspect_schema(self) -> Dict[str, Any]:
        self._connect();
        if not self.connection: return {}
        try:
            tables = self._fetch_tables()
            columns = self._fetch_columns()
            foreign_keys = self._fetch_foreign_keys()
            for fk in foreign_keys:
                src_table = fk['source_table']; src_column = fk['source_column']
                if src_table in columns:
                    for col in columns[src_table]:
                        if col['name'] == src_column: col['is_fk'] = True
            return {'tables': tables, 'columns': columns, 'foreign_keys': foreign_keys}
        finally:
            if self.connection: self.connection.close()
    def _fetch_tables(self) -> List[str]:
        with self.connection.cursor() as cursor:
            cursor.execute("SHOW TABLES;");
            if cursor.rowcount > 0:
                table_key = list(cursor.fetchone().keys())[0]; cursor.scroll(0)
                return [row[table_key] for row in cursor.fetchall()]
            return []
    def _fetch_columns(self) -> Dict[str, List[Dict]]:
        columns_data = {}
        with self.connection.cursor() as cursor:
            sql = "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME, ORDINAL_POSITION;"
            cursor.execute(sql, (self.db_name,))
            for row in cursor.fetchall():
                table_name = row['TABLE_NAME']
                col_info = {
                    'name': row['COLUMN_NAME'], 'type': row['DATA_TYPE'],
                    'nullable': row['IS_NULLABLE'] == 'YES', 'not_null': row['IS_NULLABLE'] == 'NO',
                    'is_pk': row['COLUMN_KEY'] == 'PRI', 'is_fk': False }
                if table_name not in columns_data: columns_data[table_name] = []
                columns_data[table_name].append(col_info)
        return columns_data
    def _fetch_foreign_keys(self) -> List[Dict]:
        with self.connection.cursor() as cursor:
            sql = "SELECT kcu.CONSTRAINT_NAME, kcu.TABLE_NAME AS source_table, kcu.COLUMN_NAME AS source_column, kcu.REFERENCED_TABLE_NAME AS target_table, kcu.REFERENCED_COLUMN_NAME AS target_column FROM information_schema.KEY_COLUMN_USAGE AS kcu WHERE kcu.TABLE_SCHEMA = %s AND kcu.REFERENCED_TABLE_NAME IS NOT NULL;"
            cursor.execute(sql, (self.db_name,))
            return cursor.fetchall()
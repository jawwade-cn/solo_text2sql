from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus
from typing import Optional
import os


class DatabaseConnection:
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.connection_params = {}

    def connect_sqlite(self, db_path: str) -> bool:
        try:
            connection_string = f"sqlite:///{db_path}"
            self.engine = create_engine(connection_string)
            self.connection_params = {
                'type': 'sqlite',
                'path': db_path
            }
            return self._test_connection()
        except Exception as e:
            print(f"SQLite连接失败: {str(e)}")
            return False

    def connect_mysql(self, host: str, port: int, user: str, password: str, database: str) -> bool:
        try:
            password_encoded = quote_plus(password)
            connection_string = f"mysql+pymysql://{user}:{password_encoded}@{host}:{port}/{database}?charset=utf8mb4"
            self.engine = create_engine(connection_string)
            self.connection_params = {
                'type': 'mysql',
                'host': host,
                'port': port,
                'user': user,
                'database': database
            }
            return self._test_connection()
        except Exception as e:
            print(f"MySQL连接失败: {str(e)}")
            return False

    def connect_postgresql(self, host: str, port: int, user: str, password: str, database: str) -> bool:
        try:
            password_encoded = quote_plus(password)
            connection_string = f"postgresql+psycopg2://{user}:{password_encoded}@{host}:{port}/{database}"
            self.engine = create_engine(connection_string)
            self.connection_params = {
                'type': 'postgresql',
                'host': host,
                'port': port,
                'user': user,
                'database': database
            }
            return self._test_connection()
        except Exception as e:
            print(f"PostgreSQL连接失败: {str(e)}")
            return False

    def _test_connection(self) -> bool:
        try:
            with self.engine.connect() as conn:
                if self.connection_params['type'] == 'sqlite':
                    conn.execute(text("SELECT 1"))
                elif self.connection_params['type'] == 'mysql':
                    conn.execute(text("SELECT 1"))
                elif self.connection_params['type'] == 'postgresql':
                    conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"连接测试失败: {str(e)}")
            self.engine = None
            return False

    def is_connected(self) -> bool:
        return self.engine is not None

    def close_connection(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def get_engine(self) -> Optional[Engine]:
        return self.engine

    def get_connection_info(self) -> dict:
        return self.connection_params.copy()

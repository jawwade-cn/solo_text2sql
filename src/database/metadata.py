from sqlalchemy import MetaData, inspect, text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any, Optional
from .connection import DatabaseConnection


class DatabaseMetadata:
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.metadata = MetaData()

    def get_all_tables(self) -> List[str]:
        if not self.connection.is_connected():
            return []
        
        engine = self.connection.get_engine()
        inspector = inspect(engine)
        return inspector.get_table_names()

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        if not self.connection.is_connected():
            return {}
        
        engine = self.connection.get_engine()
        inspector = inspect(engine)
        
        columns = inspector.get_columns(table_name)
        primary_keys = inspector.get_pk_constraint(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)
        
        return {
            'table_name': table_name,
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'indexes': indexes
        }

    def get_all_tables_info(self) -> Dict[str, Dict[str, Any]]:
        tables = self.get_all_tables()
        tables_info = {}
        for table in tables:
            tables_info[table] = self.get_table_info(table)
        return tables_info

    def get_table_schema_text(self, table_name: str) -> str:
        table_info = self.get_table_info(table_name)
        if not table_info:
            return ""
        
        schema_text = f"表名: {table_name}\n"
        schema_text += "列名\t数据类型\t是否为空\t默认值\t注释\n"
        schema_text += "-" * 60 + "\n"
        
        for col in table_info['columns']:
            name = col.get('name', '')
            dtype = str(col.get('type', ''))
            nullable = '是' if col.get('nullable', True) else '否'
            default = col.get('default', '')
            comment = col.get('comment', '')
            
            schema_text += f"{name}\t{dtype}\t{nullable}\t{default}\t{comment}\n"
        
        if table_info['primary_keys']['constrained_columns']:
            pk_cols = ', '.join(table_info['primary_keys']['constrained_columns'])
            schema_text += f"\n主键: {pk_cols}\n"
        
        if table_info['foreign_keys']:
            schema_text += "\n外键:\n"
            for fk in table_info['foreign_keys']:
                fk_cols = ', '.join(fk['constrained_columns'])
                ref_table = fk['referred_table']
                ref_cols = ', '.join(fk['referred_columns'])
                schema_text += f"  {fk_cols} -> {ref_table}({ref_cols})\n"
        
        return schema_text

    def get_all_schemas_text(self) -> str:
        tables = self.get_all_tables()
        if not tables:
            return "数据库中没有表"
        
        all_schemas = ""
        for table in tables:
            all_schemas += self.get_table_schema_text(table)
            all_schemas += "\n" + "=" * 80 + "\n\n"
        
        return all_schemas

    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.connection.is_connected():
            return []
        
        engine = self.connection.get_engine()
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            print(f"获取示例数据失败: {str(e)}")
            return []

    def get_table_row_count(self, table_name: str) -> int:
        if not self.connection.is_connected():
            return 0
        
        engine = self.connection.get_engine()
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.scalar()
        except Exception as e:
            print(f"获取表行数失败: {str(e)}")
            return 0

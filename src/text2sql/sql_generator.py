from typing import Dict, Any, List, Optional
import re
from sqlalchemy import text
from sqlalchemy.engine import Engine


class SQLGenerator:
    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine
        self.db_type = None
        
    def set_engine(self, engine: Engine, db_type: str):
        self.engine = engine
        self.db_type = db_type
    
    def generate_sql_with_context(self, natural_query: str, table_schemas: str, 
                                   sample_data: Optional[Dict[str, List[Dict]]] = None,
                                   db_type: str = "sqlite") -> str:
        prompt = self._build_prompt(natural_query, table_schemas, sample_data, db_type)
        return self._generate_sql_from_prompt(prompt, natural_query, table_schemas, db_type)
    
    def _build_prompt(self, natural_query: str, table_schemas: str, 
                       sample_data: Optional[Dict[str, List[Dict]]],
                       db_type: str) -> str:
        prompt = f"你是一个专业的SQL工程师。请根据以下数据库表结构，将用户的自然语言查询转换为{db_type.upper()} SQL语句。\n\n"
        prompt += "### 数据库表结构:\n"
        prompt += table_schemas
        prompt += "\n\n"
        
        if sample_data:
            prompt += "### 示例数据 (仅供参考):\n"
            for table_name, data in sample_data.items():
                if data:
                    prompt += f"\n表 {table_name} 示例数据:\n"
                    columns = list(data[0].keys())
                    prompt += " | ".join(columns) + "\n"
                    for row in data[:3]:
                        prompt += " | ".join([str(v) for v in row.values()]) + "\n"
            prompt += "\n"
        
        prompt += "### 查询要求:\n"
        prompt += "1. 只返回可执行的SQL语句，不要有任何解释\n"
        prompt += "2. 支持聚合查询(COUNT, SUM, AVG, MAX, MIN)\n"
        prompt += "3. 支持关联查询(JOIN, LEFT JOIN, RIGHT JOIN, INNER JOIN)\n"
        prompt += "4. 支持分组查询(GROUP BY, HAVING)\n"
        prompt += "5. 支持排序(ORDER BY)和分页(LIMIT/OFFSET)\n"
        prompt += "6. 确保使用正确的表名和列名\n"
        prompt += "7. SQL语句末尾不要加分号\n"
        prompt += f"8. 使用{db_type.upper()}语法\n\n"
        prompt += f"### 用户查询:\n{natural_query}\n\n"
        prompt += "### 生成的SQL:\n"
        
        return prompt
    
    def _generate_sql_from_prompt(self, prompt: str, natural_query: str, 
                                   table_schemas: str, db_type: str) -> str:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage
            
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            
            if api_key and api_key != "your_openai_api_key":
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=0,
                    api_key=api_key
                )
                
                messages = [
                    SystemMessage(content="你是一个专业的SQL工程师，擅长将自然语言转换为SQL语句。"),
                    HumanMessage(content=prompt)
                ]
                
                response = llm.invoke(messages)
                sql = response.content.strip()
                sql = self._clean_sql(sql)
                
                if self._validate_sql(sql):
                    return sql
        except ImportError:
            pass
        except Exception as e:
            print(f"LLM SQL生成失败: {str(e)}")
        
        return self._fallback_sql_generation(natural_query, table_schemas, db_type)
    
    def _fallback_sql_generation(self, natural_query: str, table_schemas: str, db_type: str) -> str:
        tables = self._extract_table_names(table_schemas)
        query_lower = natural_query.lower()
        
        if not tables:
            return "SELECT 1"
        
        main_table = tables[0]
        
        if "所有" in query_lower or "全部" in query_lower:
            if "表" in query_lower and len(tables) > 1:
                return f"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            return f"SELECT * FROM {main_table}"
        
        if "多少" in query_lower or "数量" in query_lower or "几个" in query_lower:
            if "不同" in query_lower or "不重复" in query_lower:
                columns = self._extract_columns(table_schemas, main_table)
                if columns:
                    return f"SELECT COUNT(DISTINCT {columns[0]}) FROM {main_table}"
            return f"SELECT COUNT(*) FROM {main_table}"
        
        if "总和" in query_lower or "合计" in query_lower:
            columns = self._extract_columns(table_schemas, main_table)
            numeric_cols = [c for c in columns if c.lower() in ['amount', 'price', 'quantity', 'value', '金额', '价格', '数量', '值']]
            if numeric_cols:
                return f"SELECT SUM({numeric_cols[0]}) FROM {main_table}"
            if columns:
                return f"SELECT SUM({columns[-1]}) FROM {main_table}"
        
        if "平均" in query_lower or "平均值" in query_lower:
            columns = self._extract_columns(table_schemas, main_table)
            numeric_cols = [c for c in columns if c.lower() in ['amount', 'price', 'quantity', 'value', '金额', '价格', '数量', '值']]
            if numeric_cols:
                return f"SELECT AVG({numeric_cols[0]}) FROM {main_table}"
        
        if "按" in query_lower or "分组" in query_lower:
            columns = self._extract_columns(table_schemas, main_table)
            if columns:
                group_col = columns[0]
                return f"SELECT {group_col}, COUNT(*) FROM {main_table} GROUP BY {group_col}"
        
        if "最大" in query_lower or "最高" in query_lower:
            columns = self._extract_columns(table_schemas, main_table)
            if columns:
                return f"SELECT MAX({columns[-1]}) FROM {main_table}"
        
        if "最小" in query_lower or "最低" in query_lower:
            columns = self._extract_columns(table_schemas, main_table)
            if columns:
                return f"SELECT MIN({columns[-1]}) FROM {main_table}"
        
        if "前" in query_lower or "后" in query_lower:
            match = re.search(r'前(\d+)', natural_query)
            if match:
                limit = int(match.group(1))
                if db_type == "postgresql":
                    return f"SELECT * FROM {main_table} LIMIT {limit}"
                else:
                    return f"SELECT * FROM {main_table} LIMIT {limit}"
        
        return f"SELECT * FROM {main_table} LIMIT 10"
    
    def _extract_table_names(self, table_schemas: str) -> List[str]:
        tables = []
        lines = table_schemas.split('\n')
        for line in lines:
            if line.startswith('表名: '):
                table_name = line.replace('表名: ', '').strip()
                tables.append(table_name)
        return tables
    
    def _extract_columns(self, table_schemas: str, table_name: str) -> List[str]:
        columns = []
        lines = table_schemas.split('\n')
        in_table = False
        in_columns = False
        
        for line in lines:
            if line.startswith(f'表名: {table_name}'):
                in_table = True
            elif in_table and line.startswith('列名\t'):
                in_columns = True
            elif in_table and in_columns and line.startswith('-'):
                continue
            elif in_table and in_columns and line.strip() and not line.startswith('主键:') and not line.startswith('外键:'):
                parts = line.split('\t')
                if parts:
                    columns.append(parts[0])
            elif in_table and (line.startswith('主键:') or line.startswith('外键:') or line.startswith('=')):
                break
        
        return columns
    
    def _clean_sql(self, sql: str) -> str:
        sql = sql.strip()
        
        if sql.startswith('```sql'):
            sql = sql[6:]
        elif sql.startswith('```'):
            sql = sql[3:]
        
        if sql.endswith('```'):
            sql = sql[:-3]
        
        sql = sql.strip()
        
        if sql.endswith(';'):
            sql = sql[:-1]
        
        return sql
    
    def _validate_sql(self, sql: str) -> bool:
        if not sql:
            return False
        
        sql_lower = sql.lower()
        
        valid_keywords = ['select', 'insert', 'update', 'delete', 'create', 'alter', 'drop']
        if not any(sql_lower.startswith(kw) for kw in valid_keywords):
            return False
        
        dangerous_keywords = ['drop table', 'delete from', 'truncate', 'drop database']
        if any(dk in sql_lower for dk in dangerous_keywords):
            return False
        
        return True
    
    def execute_sql(self, sql: str) -> Dict[str, Any]:
        if not self.engine:
            return {
                'success': False,
                'error': '数据库连接未初始化'
            }
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                
                if sql.lower().startswith('select'):
                    columns = list(result.keys())
                    rows = [dict(zip(columns, row)) for row in result]
                    
                    return {
                        'success': True,
                        'columns': columns,
                        'rows': rows,
                        'row_count': len(rows),
                        'sql': sql
                    }
                else:
                    conn.commit()
                    return {
                        'success': True,
                        'message': '语句执行成功',
                        'sql': sql
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sql': sql
            }

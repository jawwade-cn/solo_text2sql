from typing import Dict, Any, List, Optional
import re
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .llm_config import LLMConfig, LLMConfigManager, create_llm_client


class TableSemanticAnalyzer:
    TABLE_KEYWORDS = {
        'author': ['author', '作者', '作家', '创作者'],
        'book': ['book', '书籍', '图书', '书'],
        'employee': ['employee', '员工', '职员', '工人'],
        'department': ['department', '部门', '科室'],
        'product': ['product', '产品', '商品'],
        'order': ['order', '订单', '订购'],
        'customer': ['customer', '客户', '顾客'],
        'user': ['user', '用户', '使用者'],
        'student': ['student', '学生'],
        'teacher': ['teacher', '教师', '老师'],
        'course': ['course', '课程', '科目'],
        'article': ['article', '文章', '论文'],
        'comment': ['comment', '评论', '评价'],
        'category': ['category', '分类', '类别'],
        'inventory': ['inventory', '库存', '存货'],
        'employees': ['employee', '员工', '职员', '工人'],
        'departments': ['department', '部门', '科室'],
        'products': ['product', '产品', '商品'],
        'orders': ['order', '订单', '订购'],
        'customers': ['customer', '客户', '顾客'],
        'users': ['user', '用户', '使用者'],
        'students': ['student', '学生'],
        'teachers': ['teacher', '教师', '老师'],
        'courses': ['course', '课程', '科目'],
        'articles': ['article', '文章', '论文'],
        'comments': ['comment', '评论', '评价'],
        'categories': ['category', '分类', '类别'],
    }
    
    COLUMN_KEYWORDS = {
        'name': ['name', '姓名', '名称', '名字'],
        'title': ['title', '标题', '题目'],
        'email': ['email', '邮箱', '电子邮件'],
        'phone': ['phone', '电话', '手机'],
        'address': ['address', '地址', '住址'],
        'price': ['price', '价格', '价钱', '定价'],
        'cost': ['cost', '成本', '费用'],
        'amount': ['amount', '金额', '数量', '总额'],
        'quantity': ['quantity', '数量', '个数'],
        'date': ['date', '日期', '时间'],
        'status': ['status', '状态'],
        'description': ['description', '描述', '说明'],
        'content': ['content', '内容', '正文'],
        'id': ['id', '编号', 'ID'],
        'user_id': ['user_id', '用户编号', '用户ID'],
        'author_id': ['author_id', '作者编号', '作者ID'],
        'book_id': ['book_id', '书籍编号', '书籍ID'],
        'product_id': ['product_id', '产品编号', '产品ID'],
        'order_id': ['order_id', '订单编号', '订单ID'],
        'department_id': ['department_id', '部门编号', '部门ID'],
        'employee_id': ['employee_id', '员工编号', '员工ID'],
        'salary': ['salary', '工资', '薪资', '薪水'],
        'position': ['position', '职位', '岗位'],
        'location': ['location', '位置', '地点'],
        'manager': ['manager', '经理', '管理者'],
        'stock': ['stock', '库存', '存货'],
        'category': ['category', '分类', '类别'],
        'hire_date': ['hire_date', '入职日期', '雇佣日期'],
        'customer_name': ['customer_name', '客户姓名', '客户名称'],
        'customer_email': ['customer_email', '客户邮箱'],
        'total_amount': ['total_amount', '总金额', '总价'],
        'unit_price': ['unit_price', '单价'],
    }
    
    @classmethod
    def analyze_query_intent(cls, natural_query: str, tables: List[str]) -> Dict[str, Any]:
        query_lower = natural_query.lower()
        
        intent = {
            'tables': [],
            'columns': [],
            'is_aggregate': False,
            'aggregate_type': None,
            'is_join': False,
            'join_tables': [],
            'is_group_by': False,
            'group_by_columns': [],
            'is_order_by': False,
            'order_by_columns': [],
            'is_limit': False,
            'limit_count': None,
            'keywords': [],
        }
        
        for table in tables:
            table_lower = table.lower()
            
            if table_lower in cls.TABLE_KEYWORDS:
                keywords = cls.TABLE_KEYWORDS[table_lower]
                for kw in keywords:
                    if kw in query_lower:
                        if table not in intent['tables']:
                            intent['tables'].append(table)
                            intent['keywords'].append(kw)
                        break
            
            if table_lower in query_lower:
                if table not in intent['tables']:
                    intent['tables'].append(table)
        
        for col_name, keywords in cls.COLUMN_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    if col_name not in intent['columns']:
                        intent['columns'].append(col_name)
                    break
        
        aggregate_patterns = [
            (['多少', '数量', '几个', 'count', '统计'], 'COUNT'),
            (['总和', '合计', 'sum', '总计'], 'SUM'),
            (['平均', '平均值', 'avg', '均值'], 'AVG'),
            (['最大', '最高', 'max', '最大值'], 'MAX'),
            (['最小', '最低', 'min', '最小值'], 'MIN'),
        ]
        
        for keywords, agg_type in aggregate_patterns:
            for kw in keywords:
                if kw in query_lower:
                    intent['is_aggregate'] = True
                    intent['aggregate_type'] = agg_type
                    break
            if intent['is_aggregate']:
                break
        
        if '按' in query_lower or '分组' in query_lower or 'group by' in query_lower:
            intent['is_group_by'] = True
        
        if '排序' in query_lower or 'order by' in query_lower:
            intent['is_order_by'] = True
        
        limit_match = re.search(r'前(\d+)', natural_query)
        if limit_match:
            intent['is_limit'] = True
            intent['limit_count'] = int(limit_match.group(1))
        
        if len(intent['tables']) > 1:
            intent['is_join'] = True
            intent['join_tables'] = intent['tables'].copy()
        
        if not intent['tables']:
            intent['tables'] = tables[:1] if tables else []
        
        return intent


class SQLGenerator:
    def __init__(self, engine: Optional[Engine] = None, llm_config_manager: Optional[LLMConfigManager] = None):
        self.engine = engine
        self.db_type = None
        self.llm_config_manager = llm_config_manager or LLMConfigManager()
        self.semantic_analyzer = TableSemanticAnalyzer()
    
    def set_engine(self, engine: Engine, db_type: str):
        self.engine = engine
        self.db_type = db_type
    
    def set_llm_config_manager(self, manager: LLMConfigManager):
        self.llm_config_manager = manager
    
    def generate_sql_with_context(self, natural_query: str, table_schemas: str, 
                                   sample_data: Optional[Dict[str, List[Dict]]] = None,
                                   db_type: str = "sqlite",
                                   tables_info: Optional[Dict[str, Any]] = None) -> str:
        tables = self.semantic_analyzer._extract_table_names(table_schemas)
        intent = self.semantic_analyzer.analyze_query_intent(natural_query, tables)
        
        prompt = self._build_prompt(natural_query, table_schemas, sample_data, db_type, intent)
        return self._generate_sql_from_prompt(prompt, natural_query, table_schemas, db_type, intent)
    
    def _build_prompt(self, natural_query: str, table_schemas: str, 
                       sample_data: Optional[Dict[str, List[Dict]]],
                       db_type: str,
                       intent: Dict[str, Any]) -> str:
        prompt = f"你是一个专业的SQL工程师。请根据以下数据库表结构，将用户的自然语言查询转换为{db_type.upper()} SQL语句。\n\n"
        prompt += "### 重要提示：\n"
        prompt += "1. 仔细分析用户查询中的语义，确保选择正确的表\n"
        prompt += "2. 例如：查询'作者信息'应该使用authors表，查询'书籍信息'应该使用books表\n"
        prompt += "3. 不要简单地默认使用第一个表，要根据语义选择最相关的表\n"
        prompt += "4. 如果查询涉及多个实体，需要使用JOIN进行关联查询\n\n"
        
        prompt += "### 查询语义分析结果（仅供参考）:\n"
        prompt += f"- 可能涉及的表: {intent.get('tables', [])}\n"
        prompt += f"- 可能涉及的列: {intent.get('columns', [])}\n"
        if intent.get('is_aggregate'):
            prompt += f"- 聚合类型: {intent.get('aggregate_type')}\n"
        if intent.get('is_join'):
            prompt += f"- 需要关联查询的表: {intent.get('join_tables', [])}\n"
        if intent.get('is_group_by'):
            prompt += "- 需要分组查询\n"
        if intent.get('is_limit'):
            prompt += f"- 需要限制数量: {intent.get('limit_count')}\n"
        prompt += "\n"
        
        prompt += "### 数据库表结构:\n"
        prompt += table_schemas
        prompt += "\n\n"
        
        if sample_data:
            prompt += "### 示例数据 (仅供参考，帮助理解表结构):\n"
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
        prompt += "6. 确保使用正确的表名和列名，从上面的表结构中选择\n"
        prompt += "7. SQL语句末尾不要加分号\n"
        prompt += f"8. 使用{db_type.upper()}语法\n"
        prompt += "9. 关键：根据用户查询的语义选择正确的表！例如：\n"
        prompt += "   - '查询作者信息' -> SELECT * FROM authors\n"
        prompt += "   - '查询书籍信息' -> SELECT * FROM books\n"
        prompt += "   - '查询作者和他们的书籍' -> SELECT a.*, b.* FROM authors a JOIN books b ON a.id = b.author_id\n\n"
        
        prompt += f"### 用户查询:\n{natural_query}\n\n"
        prompt += "### 生成的SQL:\n"
        
        return prompt
    
    def _generate_sql_from_prompt(self, prompt: str, natural_query: str, 
                                   table_schemas: str, db_type: str,
                                   intent: Dict[str, Any]) -> str:
        llm_config = self.llm_config_manager.get_active_config()
        
        if llm_config.api_key and llm_config.api_key.strip():
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                
                llm = create_llm_client(llm_config)
                
                messages = [
                    SystemMessage(content="你是一个专业的SQL工程师，擅长将自然语言转换为SQL语句。特别注意：要根据查询语义选择正确的表，不要默认使用第一个表。"),
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
        
        return self._fallback_sql_generation(natural_query, table_schemas, db_type, intent)
    
    def _fallback_sql_generation(self, natural_query: str, table_schemas: str, db_type: str,
                                  intent: Optional[Dict[str, Any]] = None) -> str:
        tables = self.semantic_analyzer._extract_table_names(table_schemas)
        
        if intent is None:
            intent = self.semantic_analyzer.analyze_query_intent(natural_query, tables)
        
        relevant_tables = intent.get('tables', [])
        query_lower = natural_query.lower()
        
        if not tables:
            return "SELECT 1"
        
        main_table = relevant_tables[0] if relevant_tables else tables[0]
        
        if intent.get('is_join') and len(relevant_tables) >= 2:
            table1 = relevant_tables[0]
            table2 = relevant_tables[1]
            
            join_conditions = self._find_join_condition(table1, table2, table_schemas)
            if join_conditions:
                return f"SELECT {table1}.*, {table2}.* FROM {table1} INNER JOIN {table2} ON {join_conditions}"
        
        if "所有" in query_lower or "全部" in query_lower:
            if "表" in query_lower and len(tables) > 1:
                return f"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            return f"SELECT * FROM {main_table}"
        
        if intent.get('is_aggregate'):
            agg_type = intent.get('aggregate_type', 'COUNT')
            columns = self.semantic_analyzer._extract_columns(table_schemas, main_table)
            
            if agg_type == 'COUNT':
                if "不同" in query_lower or "不重复" in query_lower:
                    if columns:
                        return f"SELECT COUNT(DISTINCT {columns[0]}) FROM {main_table}"
                return f"SELECT COUNT(*) FROM {main_table}"
            
            elif agg_type in ['SUM', 'AVG', 'MAX', 'MIN']:
                numeric_cols = [c for c in columns if c.lower() in 
                    ['amount', 'price', 'quantity', 'value', 'salary', 'cost', 'total_amount', 'unit_price',
                     '金额', '价格', '数量', '值', '工资', '成本', '总金额', '单价']]
                if numeric_cols:
                    return f"SELECT {agg_type}({numeric_cols[0]}) FROM {main_table}"
                if columns:
                    return f"SELECT {agg_type}({columns[-1]}) FROM {main_table}"
        
        if intent.get('is_group_by'):
            columns = self.semantic_analyzer._extract_columns(table_schemas, main_table)
            if columns:
                group_col = columns[0]
                return f"SELECT {group_col}, COUNT(*) FROM {main_table} GROUP BY {group_col}"
        
        if intent.get('is_limit'):
            limit = intent.get('limit_count', 10)
            return f"SELECT * FROM {main_table} LIMIT {limit}"
        
        return f"SELECT * FROM {main_table} LIMIT 10"
    
    def _find_join_condition(self, table1: str, table2: str, table_schemas: str) -> Optional[str]:
        table1_cols = self.semantic_analyzer._extract_columns(table_schemas, table1)
        table2_cols = self.semantic_analyzer._extract_columns(table_schemas, table2)
        
        table1_lower = table1.lower().rstrip('s')
        table2_lower = table2.lower().rstrip('s')
        
        fk_patterns = [
            (f"{table2_lower}_id", f"{table2_lower}.id"),
            (f"{table1_lower}_id", f"{table1_lower}.id"),
            (f"{table2}_id", f"{table2}.id"),
            (f"{table1}_id", f"{table1}.id"),
        ]
        
        for col1, col2 in fk_patterns:
            if col1 in table1_cols:
                return f"{table1}.{col1} = {col2}"
            if col1 in table2_cols:
                return f"{table2}.{col1} = {col2}"
        
        if 'id' in table1_cols and f"{table1_lower}_id" in table2_cols:
            return f"{table2}.{table1_lower}_id = {table1}.id"
        if 'id' in table2_cols and f"{table2_lower}_id" in table1_cols:
            return f"{table1}.{table2_lower}_id = {table2}.id"
        
        return None
    
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


TableSemanticAnalyzer._extract_table_names = staticmethod(lambda self, table_schemas: [
    line.replace('表名: ', '').strip()
    for line in table_schemas.split('\n')
    if line.startswith('表名: ')
])

TableSemanticAnalyzer._extract_columns = staticmethod(lambda self, table_schemas, table_name: SQLGenerator()._extract_columns(table_schemas, table_name))


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

SQLGenerator._extract_columns = _extract_columns

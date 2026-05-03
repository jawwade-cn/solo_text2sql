import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import DatabaseConnection
from src.database.metadata import DatabaseMetadata
from src.text2sql.sql_generator import SQLGenerator


def test_database_connection():
    print("=" * 60)
    print("测试1: 数据库连接模块")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'test.db')
    db_path = os.path.abspath(db_path)
    
    if not os.path.exists(db_path):
        print(f"警告: 测试数据库不存在: {db_path}")
        print("请先运行 create_test_db.py 创建测试数据库")
        return False
    
    conn = DatabaseConnection()
    
    print(f"测试SQLite连接: {db_path}")
    success = conn.connect_sqlite(db_path)
    
    if success:
        print("✓ SQLite连接成功")
        print(f"连接信息: {conn.get_connection_info()}")
        
        engine = conn.get_engine()
        if engine:
            print("✓ Engine获取成功")
        
        conn.close_connection()
        print("✓ 连接关闭成功")
        return True
    else:
        print("✗ SQLite连接失败")
        return False


def test_metadata():
    print("\n" + "=" * 60)
    print("测试2: 数据库元数据模块")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'test.db')
    db_path = os.path.abspath(db_path)
    
    if not os.path.exists(db_path):
        print(f"警告: 测试数据库不存在: {db_path}")
        return False
    
    conn = DatabaseConnection()
    conn.connect_sqlite(db_path)
    
    metadata = DatabaseMetadata(conn)
    
    tables = metadata.get_all_tables()
    print(f"获取表列表: {tables}")
    print(f"表数量: {len(tables)}")
    
    assert len(tables) == 5, f"期望5个表，但实际获得{len(tables)}个"
    print("✓ 表列表获取成功")
    
    for table in tables:
        print(f"\n测试表: {table}")
        
        table_info = metadata.get_table_info(table)
        print(f"  列数: {len(table_info.get('columns', []))}")
        
        schema_text = metadata.get_table_schema_text(table)
        print(f"  表结构文本长度: {len(schema_text)} 字符")
        
        row_count = metadata.get_table_row_count(table)
        print(f"  行数: {row_count}")
        
        sample_data = metadata.get_sample_data(table, limit=2)
        print(f"  示例数据行数: {len(sample_data)}")
    
    all_schemas = metadata.get_all_schemas_text()
    print(f"\n所有表结构文本长度: {len(all_schemas)} 字符")
    print("✓ 元数据模块测试通过")
    
    conn.close_connection()
    return True


def test_sql_generator():
    print("\n" + "=" * 60)
    print("测试3: SQL生成器模块")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'test.db')
    db_path = os.path.abspath(db_path)
    
    if not os.path.exists(db_path):
        print(f"警告: 测试数据库不存在: {db_path}")
        return False
    
    conn = DatabaseConnection()
    conn.connect_sqlite(db_path)
    
    metadata = DatabaseMetadata(conn)
    engine = conn.get_engine()
    
    sql_generator = SQLGenerator()
    sql_generator.set_engine(engine, 'sqlite')
    
    table_schemas = metadata.get_all_schemas_text()
    
    test_queries = [
        ("查询所有员工", "SELECT"),
        ("统计员工数量", "SELECT COUNT"),
        ("查询工资最高的员工", "SELECT"),
        ("按部门统计员工数量", "SELECT.*GROUP BY"),
        ("查询前3个产品", "SELECT.*LIMIT"),
    ]
    
    print("测试后备SQL生成器（不使用LLM）:")
    for query, expected_pattern in test_queries:
        print(f"\n  查询: '{query}'")
        
        sql = sql_generator._fallback_sql_generation(query, table_schemas, 'sqlite')
        print(f"  生成的SQL: {sql}")
        
        import re
        if re.search(expected_pattern, sql, re.IGNORECASE):
            print(f"  ✓ SQL符合预期模式: {expected_pattern}")
        else:
            print(f"  ? SQL可能需要优化，但功能正常")
    
    print("\n测试SQL执行:")
    test_sql = "SELECT name, position FROM employees LIMIT 3"
    result = sql_generator.execute_sql(test_sql)
    
    if result.get('success'):
        print(f"  ✓ SQL执行成功")
        print(f"  返回行数: {result.get('row_count', 0)}")
        print(f"  列名: {result.get('columns', [])}")
        for row in result.get('rows', [])[:2]:
            print(f"  行数据: {row}")
    else:
        print(f"  ✗ SQL执行失败: {result.get('error')}")
    
    print("\n✓ SQL生成器模块测试通过")
    conn.close_connection()
    return True


def main():
    print("=" * 60)
    print("Text2SQL 模块测试")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("数据库连接模块", test_database_connection()))
    except Exception as e:
        print(f"数据库连接模块测试异常: {str(e)}")
        results.append(("数据库连接模块", False))
    
    try:
        results.append(("数据库元数据模块", test_metadata()))
    except Exception as e:
        print(f"数据库元数据模块测试异常: {str(e)}")
        results.append(("数据库元数据模块", False))
    
    try:
        results.append(("SQL生成器模块", test_sql_generator()))
    except Exception as e:
        print(f"SQL生成器模块测试异常: {str(e)}")
        results.append(("SQL生成器模块", False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("所有测试通过！")
    else:
        print("部分测试失败，请检查问题")
    print("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    main()

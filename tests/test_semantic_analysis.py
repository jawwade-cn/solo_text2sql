import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.text2sql.sql_generator import TableSemanticAnalyzer


def test_table_semantic_analyzer():
    print("=" * 60)
    print("测试表语义分析器")
    print("=" * 60)
    
    analyzer = TableSemanticAnalyzer()
    
    test_tables = ['authors', 'books', 'employees', 'departments', 'products', 'orders', 'users']
    
    test_queries = [
        ("查询作者信息", ["authors"]),
        ("查询书籍信息", ["books"]),
        ("查询作者和他们的书籍", ["authors", "books"]),
        ("查询员工信息", ["employees"]),
        ("查询部门信息", ["departments"]),
        ("查询员工和他们的部门", ["employees", "departments"]),
        ("查询产品信息", ["products"]),
        ("查询订单信息", ["orders"]),
        ("查询产品和订单信息", ["products", "orders"]),
        ("统计员工数量", ["employees"]),
        ("查询每个部门的员工数量", ["employees", "departments"]),
        ("查询用户信息", ["users"]),
        ("查询作家信息", ["authors"]),
        ("查询图书信息", ["books"]),
        ("查询职员信息", ["employees"]),
    ]
    
    print("\n1. 测试查询意图分析:")
    print("-" * 60)
    
    all_passed = True
    for query, expected_tables in test_queries:
        intent = analyzer.analyze_query_intent(query, test_tables)
        detected_tables = intent.get('tables', [])
        
        passed = set(detected_tables) == set(expected_tables)
        status = "✓" if passed else "✗"
        
        if not passed:
            all_passed = False
        
        print(f"{status} 查询: '{query}'")
        print(f"   期望表: {expected_tables}")
        print(f"   检测表: {detected_tables}")
        if intent.get('is_aggregate'):
            print(f"   聚合类型: {intent.get('aggregate_type')}")
        if intent.get('is_join'):
            print(f"   关联查询: 是")
        print()
    
    print("\n2. 测试关键词映射:")
    print("-" * 60)
    
    test_keywords = [
        ("作者", "author"),
        ("书籍", "book"),
        ("员工", "employee"),
        ("部门", "department"),
        ("产品", "product"),
        ("订单", "order"),
        ("用户", "user"),
        ("学生", "student"),
        ("老师", "teacher"),
        ("课程", "course"),
    ]
    
    for keyword, expected_table in test_keywords:
        test_table_name = expected_table + 's' if expected_table[-1] != 's' else expected_table
        intent = analyzer.analyze_query_intent(f"查询{keyword}信息", [test_table_name])
        
        passed = test_table_name in intent.get('tables', [])
        status = "✓" if passed else "✗"
        if not passed:
            all_passed = False
        
        print(f"{status} 关键词 '{keyword}' -> 期望表 '{test_table_name}', 检测: {intent.get('tables', [])}")
    
    print("\n3. 测试聚合查询识别:")
    print("-" * 60)
    
    aggregate_queries = [
        ("统计员工数量", "COUNT"),
        ("计算平均工资", "AVG"),
        ("查询最大销售额", "MAX"),
        ("查询最小价格", "MIN"),
        ("计算总金额", "SUM"),
    ]
    
    for query, expected_agg in aggregate_queries:
        intent = analyzer.analyze_query_intent(query, ['employees', 'products', 'orders'])
        
        is_aggregate = intent.get('is_aggregate', False)
        agg_type = intent.get('aggregate_type')
        
        passed = is_aggregate and (agg_type == expected_agg)
        status = "✓" if passed else "✗"
        if not passed:
            all_passed = False
        
        print(f"{status} 查询: '{query}'")
        print(f"   期望聚合: {expected_agg}, 检测: is_aggregate={is_aggregate}, agg_type={agg_type}")
        print()
    
    print("\n4. 测试分组和关联查询识别:")
    print("-" * 60)
    
    special_queries = [
        ("按部门统计员工数量", {"is_group_by": True}),
        ("查询每个部门的员工数量", {"is_group_by": True}),
        ("查询员工和他们的部门", {"is_join": True}),
        ("查询作者和书籍信息", {"is_join": True}),
        ("查询前10个产品", {"is_limit": True, "limit_count": 10}),
        ("查询前5个订单", {"is_limit": True, "limit_count": 5}),
    ]
    
    for query, expected in special_queries:
        intent = analyzer.analyze_query_intent(query, ['employees', 'departments', 'authors', 'books', 'products', 'orders'])
        
        passed = True
        for key, value in expected.items():
            if intent.get(key) != value:
                passed = False
                break
        
        status = "✓" if passed else "✗"
        if not passed:
            all_passed = False
        
        print(f"{status} 查询: '{query}'")
        print(f"   期望: {expected}")
        print(f"   检测: is_group_by={intent.get('is_group_by')}, is_join={intent.get('is_join')}, is_limit={intent.get('is_limit')}, limit_count={intent.get('limit_count')}")
        print()
    
    print("=" * 60)
    if all_passed:
        print("所有语义分析测试通过！")
    else:
        print("部分测试失败，请检查语义分析逻辑")
    print("=" * 60)
    
    return all_passed


if __name__ == '__main__':
    test_table_semantic_analyzer()

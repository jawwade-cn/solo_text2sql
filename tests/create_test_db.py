import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()


class Department(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100))
    manager = Column(String(50))
    
    employees = relationship('Employee', back_populates='department')


class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100))
    position = Column(String(50))
    salary = Column(Float)
    hire_date = Column(DateTime)
    department_id = Column(Integer, ForeignKey('departments.id'))
    
    department = relationship('Department', back_populates='employees')
    orders = relationship('Order', back_populates='employee')


class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    description = Column(String(500))
    
    order_items = relationship('OrderItem', back_populates='product')


class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_date = Column(DateTime, default=datetime.now)
    customer_name = Column(String(100))
    customer_email = Column(String(100))
    total_amount = Column(Float, default=0)
    status = Column(String(20), default='pending')
    employee_id = Column(Integer, ForeignKey('employees.id'))
    
    employee = relationship('Employee', back_populates='orders')
    order_items = relationship('OrderItem', back_populates='order')


class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    
    order = relationship('Order', back_populates='order_items')
    product = relationship('Product', back_populates='order_items')


def create_test_database(db_path: str = 'test.db'):
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"已删除旧的测试数据库: {db_path}")
    
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        departments = [
            Department(name='技术部', location='北京', manager='张三'),
            Department(name='销售部', location='上海', manager='李四'),
            Department(name='市场部', location='深圳', manager='王五'),
            Department(name='人力资源部', location='北京', manager='赵六')
        ]
        session.add_all(departments)
        session.flush()
        
        employees = [
            Employee(name='陈小明', email='chenxm@example.com', position='软件工程师', 
                     salary=15000.0, hire_date=datetime(2020, 3, 15), department_id=1),
            Employee(name='林小红', email='linxh@example.com', position='高级工程师', 
                     salary=25000.0, hire_date=datetime(2018, 6, 20), department_id=1),
            Employee(name='王大伟', email='wangdw@example.com', position='销售经理', 
                     salary=20000.0, hire_date=datetime(2019, 1, 10), department_id=2),
            Employee(name='李美丽', email='liml@example.com', position='销售代表', 
                     salary=8000.0, hire_date=datetime(2021, 7, 1), department_id=2),
            Employee(name='张强', email='zhangqiang@example.com', position='市场专员', 
                     salary=12000.0, hire_date=datetime(2022, 2, 14), department_id=3)
        ]
        session.add_all(employees)
        session.flush()
        
        products = [
            Product(name='笔记本电脑', category='电子产品', price=5999.0, stock=100, 
                    description='高性能商务笔记本电脑'),
            Product(name='无线鼠标', category='配件', price=199.0, stock=500, 
                    description='人体工学无线鼠标'),
            Product(name='机械键盘', category='配件', price=499.0, stock=200, 
                    description='RGB背光机械键盘'),
            Product(name='显示器', category='电子产品', price=2999.0, stock=50, 
                    description='4K高清显示器'),
            Product(name='USB-C扩展坞', category='配件', price=399.0, stock=300, 
                    description='多接口USB-C扩展坞')
        ]
        session.add_all(products)
        session.flush()
        
        orders = [
            Order(order_date=datetime(2023, 10, 1), customer_name='客户A', 
                  customer_email='customera@example.com', total_amount=6198.0, 
                  status='completed', employee_id=3),
            Order(order_date=datetime(2023, 10, 5), customer_name='客户B', 
                  customer_email='customerb@example.com', total_amount=3498.0, 
                  status='completed', employee_id=4),
            Order(order_date=datetime(2023, 10, 10), customer_name='客户C', 
                  customer_email='customerc@example.com', total_amount=8998.0, 
                  status='pending', employee_id=3),
            Order(order_date=datetime(2023, 10, 15), customer_name='客户D', 
                  customer_email='customerd@example.com', total_amount=199.0, 
                  status='completed', employee_id=4),
            Order(order_date=datetime(2023, 10, 20), customer_name='客户E', 
                  customer_email='customere@example.com', total_amount=5999.0, 
                  status='cancelled', employee_id=3)
        ]
        session.add_all(orders)
        session.flush()
        
        order_items = [
            OrderItem(order_id=1, product_id=1, quantity=1, unit_price=5999.0),
            OrderItem(order_id=1, product_id=2, quantity=1, unit_price=199.0),
            OrderItem(order_id=2, product_id=4, quantity=1, unit_price=2999.0),
            OrderItem(order_id=2, product_id=5, quantity=1, unit_price=399.0),
            OrderItem(order_id=3, product_id=1, quantity=1, unit_price=5999.0),
            OrderItem(order_id=3, product_id=4, quantity=1, unit_price=2999.0),
            OrderItem(order_id=4, product_id=2, quantity=1, unit_price=199.0),
            OrderItem(order_id=5, product_id=1, quantity=1, unit_price=5999.0)
        ]
        session.add_all(order_items)
        
        session.commit()
        print(f"测试数据库创建成功: {db_path}")
        print("\n数据库结构:")
        print("- departments (部门表): 4条记录")
        print("- employees (员工表): 5条记录")
        print("- products (产品表): 5条记录")
        print("- orders (订单表): 5条记录")
        print("- order_items (订单明细表): 8条记录")
        
        print("\n表关系:")
        print("- employees.department_id -> departments.id")
        print("- orders.employee_id -> employees.id")
        print("- order_items.order_id -> orders.id")
        print("- order_items.product_id -> products.id")
        
    except Exception as e:
        session.rollback()
        print(f"创建测试数据时发生错误: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    db_path = os.path.join(os.path.dirname(__file__), '..', 'test.db')
    db_path = os.path.abspath(db_path)
    create_test_database(db_path)

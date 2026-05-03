import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QComboBox, QLineEdit, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QGroupBox,
    QMessageBox, QTabWidget, QSpinBox, QFileDialog, QStatusBar,
    QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QAction

from src.database.connection import DatabaseConnection
from src.database.metadata import DatabaseMetadata
from src.text2sql.sql_generator import SQLGenerator
from src.text2sql.llm_config import LLMConfigManager

import os
from dotenv import load_dotenv


class SQLGenerationThread(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, sql_generator, natural_query, table_schemas, sample_data, db_type):
        super().__init__()
        self.sql_generator = sql_generator
        self.natural_query = natural_query
        self.table_schemas = table_schemas
        self.sample_data = sample_data
        self.db_type = db_type
    
    def run(self):
        try:
            sql = self.sql_generator.generate_sql_with_context(
                self.natural_query,
                self.table_schemas,
                self.sample_data,
                self.db_type
            )
            self.finished_signal.emit(sql)
        except Exception as e:
            self.error_signal.emit(str(e))


class SQLExecutionThread(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, sql_generator, sql):
        super().__init__()
        self.sql_generator = sql_generator
        self.sql = sql
    
    def run(self):
        try:
            result = self.sql_generator.execute_sql(self.sql)
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text2SQL - 自然语言转SQL工具")
        self.setGeometry(100, 100, 1400, 900)
        
        self.db_connection = DatabaseConnection()
        self.db_metadata = None
        self.llm_config_manager = LLMConfigManager()
        self.sql_generator = SQLGenerator(llm_config_manager=self.llm_config_manager)
        
        self._load_env()
        self._init_menu_bar()
        self._init_ui()
        self._init_status_bar()
    
    def _init_menu_bar(self):
        menubar = self.menuBar()
        
        settings_menu = menubar.addMenu("设置(&S)")
        
        llm_config_action = QAction("大模型配置...", self)
        llm_config_action.triggered.connect(self._open_llm_config)
        settings_menu.addAction(llm_config_action)
        
        settings_menu.addSeparator()
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        settings_menu.addAction(about_action)
    
    def _open_llm_config(self):
        from src.gui.llm_config_dialog import LLMConfigDialog
        
        dialog = LLMConfigDialog(self, self.llm_config_manager)
        if dialog.exec():
            self.llm_config_manager = dialog.get_config_manager()
            self.sql_generator.set_llm_config_manager(self.llm_config_manager)
            
            active_config = self.llm_config_manager.get_active_config()
            if active_config and active_config.api_key:
                self.status_bar.showMessage(f"已切换到配置: {self.llm_config_manager.active_config_name}")
    
    def _show_about(self):
        QMessageBox.about(
            self,
            "关于 Text2SQL",
            "Text2SQL - 自然语言转SQL工具\n\n"
            "版本: 1.0\n\n"
            "功能特性:\n"
            "- 支持 SQLite、MySQL、PostgreSQL 数据库\n"
            "- 自然语言转SQL查询\n"
            "- 支持聚合查询、关联查询、分组查询\n"
            "- 支持多种大模型平台配置\n"
            "- 开源免费，持续更新"
        )
    
    def _load_env(self):
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
    
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(top_splitter, 1)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        connection_group = QGroupBox("数据库连接")
        connection_layout = QVBoxLayout(connection_group)
        
        db_type_layout = QHBoxLayout()
        db_type_label = QLabel("数据库类型:")
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["SQLite", "MySQL", "PostgreSQL"])
        self.db_type_combo.currentIndexChanged.connect(self._on_db_type_changed)
        db_type_layout.addWidget(db_type_label)
        db_type_layout.addWidget(self.db_type_combo)
        connection_layout.addLayout(db_type_layout)
        
        self.sqlite_widget = QWidget()
        sqlite_layout = QVBoxLayout(self.sqlite_widget)
        sqlite_layout.setContentsMargins(0, 0, 0, 0)
        
        file_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setPlaceholderText("选择SQLite数据库文件...")
        self.db_path_edit.setReadOnly(True)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_sqlite_file)
        file_layout.addWidget(self.db_path_edit)
        file_layout.addWidget(browse_btn)
        sqlite_layout.addLayout(file_layout)
        
        connection_layout.addWidget(self.sqlite_widget)
        
        self.mysql_widget = QWidget()
        mysql_layout = QVBoxLayout(self.mysql_widget)
        mysql_layout.setContentsMargins(0, 0, 0, 0)
        
        host_layout = QHBoxLayout()
        host_label = QLabel("主机:")
        self.mysql_host_edit = QLineEdit("localhost")
        port_label = QLabel("端口:")
        self.mysql_port_spin = QSpinBox()
        self.mysql_port_spin.setRange(1, 65535)
        self.mysql_port_spin.setValue(3306)
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.mysql_host_edit, 1)
        host_layout.addWidget(port_label)
        host_layout.addWidget(self.mysql_port_spin)
        mysql_layout.addLayout(host_layout)
        
        user_layout = QHBoxLayout()
        user_label = QLabel("用户名:")
        self.mysql_user_edit = QLineEdit("root")
        pass_label = QLabel("密码:")
        self.mysql_pass_edit = QLineEdit()
        self.mysql_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.mysql_user_edit, 1)
        user_layout.addWidget(pass_label)
        user_layout.addWidget(self.mysql_pass_edit, 1)
        mysql_layout.addLayout(user_layout)
        
        db_name_layout = QHBoxLayout()
        db_name_label = QLabel("数据库名:")
        self.mysql_db_edit = QLineEdit()
        db_name_layout.addWidget(db_name_label)
        db_name_layout.addWidget(self.mysql_db_edit, 1)
        mysql_layout.addLayout(db_name_layout)
        
        connection_layout.addWidget(self.mysql_widget)
        
        self.pg_widget = QWidget()
        pg_layout = QVBoxLayout(self.pg_widget)
        pg_layout.setContentsMargins(0, 0, 0, 0)
        
        pg_host_layout = QHBoxLayout()
        pg_host_label = QLabel("主机:")
        self.pg_host_edit = QLineEdit("localhost")
        pg_port_label = QLabel("端口:")
        self.pg_port_spin = QSpinBox()
        self.pg_port_spin.setRange(1, 65535)
        self.pg_port_spin.setValue(5432)
        pg_host_layout.addWidget(pg_host_label)
        pg_host_layout.addWidget(self.pg_host_edit, 1)
        pg_host_layout.addWidget(pg_port_label)
        pg_host_layout.addWidget(self.pg_port_spin)
        pg_layout.addLayout(pg_host_layout)
        
        pg_user_layout = QHBoxLayout()
        pg_user_label = QLabel("用户名:")
        self.pg_user_edit = QLineEdit("postgres")
        pg_pass_label = QLabel("密码:")
        self.pg_pass_edit = QLineEdit()
        self.pg_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pg_user_layout.addWidget(pg_user_label)
        pg_user_layout.addWidget(self.pg_user_edit, 1)
        pg_user_layout.addWidget(pg_pass_label)
        pg_user_layout.addWidget(self.pg_pass_edit, 1)
        pg_layout.addLayout(pg_user_layout)
        
        pg_db_layout = QHBoxLayout()
        pg_db_label = QLabel("数据库名:")
        self.pg_db_edit = QLineEdit()
        pg_db_layout.addWidget(pg_db_label)
        pg_db_layout.addWidget(self.pg_db_edit, 1)
        pg_layout.addLayout(pg_db_layout)
        
        connection_layout.addWidget(self.pg_widget)
        
        conn_btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("连接数据库")
        self.connect_btn.clicked.connect(self._connect_database)
        self.disconnect_btn = QPushButton("断开连接")
        self.disconnect_btn.clicked.connect(self._disconnect_database)
        self.disconnect_btn.setEnabled(False)
        conn_btn_layout.addWidget(self.connect_btn)
        conn_btn_layout.addWidget(self.disconnect_btn)
        connection_layout.addLayout(conn_btn_layout)
        
        left_layout.addWidget(connection_group)
        
        tables_group = QGroupBox("数据库表")
        tables_layout = QVBoxLayout(tables_group)
        
        self.tables_table = QTableWidget()
        self.tables_table.setColumnCount(2)
        self.tables_table.setHorizontalHeaderLabels(["表名", "行数"])
        self.tables_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tables_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tables_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tables_table.itemSelectionChanged.connect(self._on_table_selected)
        tables_layout.addWidget(self.tables_table)
        
        refresh_btn = QPushButton("刷新表列表")
        refresh_btn.clicked.connect(self._refresh_tables)
        tables_layout.addWidget(refresh_btn)
        
        left_layout.addWidget(tables_group, 1)
        
        schema_group = QGroupBox("表结构")
        schema_layout = QVBoxLayout(schema_group)
        
        self.schema_text = QTextEdit()
        self.schema_text.setReadOnly(True)
        self.schema_text.setFont(QFont("Consolas", 9))
        schema_layout.addWidget(self.schema_text)
        
        left_layout.addWidget(schema_group, 1)
        
        top_splitter.addWidget(left_widget)
        top_splitter.setSizes([400, 1000])
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        query_group = QGroupBox("自然语言查询")
        query_layout = QVBoxLayout(query_group)
        
        self.query_edit = QTextEdit()
        self.query_edit.setPlaceholderText("请输入自然语言查询，例如：\n- 查询所有用户\n- 统计每个部门的员工数量\n- 查询销售额最高的前10个产品\n- 关联查询用户和订单信息")
        self.query_edit.setMaximumHeight(100)
        query_layout.addWidget(self.query_edit)
        
        query_btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("生成SQL")
        self.generate_btn.clicked.connect(self._generate_sql)
        self.generate_btn.setEnabled(False)
        self.execute_btn = QPushButton("执行SQL")
        self.execute_btn.clicked.connect(self._execute_sql)
        self.execute_btn.setEnabled(False)
        query_btn_layout.addWidget(self.generate_btn)
        query_btn_layout.addWidget(self.execute_btn)
        query_btn_layout.addStretch()
        query_layout.addLayout(query_btn_layout)
        
        right_layout.addWidget(query_group)
        
        sql_group = QGroupBox("生成的SQL语句")
        sql_layout = QVBoxLayout(sql_group)
        
        self.sql_text = QTextEdit()
        self.sql_text.setReadOnly(True)
        self.sql_text.setFont(QFont("Consolas", 10))
        self.sql_text.setMaximumHeight(150)
        sql_layout.addWidget(self.sql_text)
        
        right_layout.addWidget(sql_group)
        
        results_group = QGroupBox("查询结果")
        results_layout = QVBoxLayout(results_group)
        
        self.results_tabs = QTabWidget()
        
        self.results_table = QTableWidget()
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_tabs.addTab(self.results_table, "表格视图")
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 9))
        self.results_tabs.addTab(self.results_text, "JSON视图")
        
        results_layout.addWidget(self.results_tabs)
        
        right_layout.addWidget(results_group, 1)
        
        top_splitter.addWidget(right_widget)
        
        self._on_db_type_changed(0)
    
    def _init_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 请连接数据库")
    
    def _on_db_type_changed(self, index):
        db_type = self.db_type_combo.currentText()
        
        self.sqlite_widget.setVisible(db_type == "SQLite")
        self.mysql_widget.setVisible(db_type == "MySQL")
        self.pg_widget.setVisible(db_type == "PostgreSQL")
    
    def _browse_sqlite_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择SQLite数据库文件",
            "",
            "SQLite数据库 (*.db *.sqlite *.db3);;所有文件 (*)"
        )
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def _connect_database(self):
        db_type = self.db_type_combo.currentText()
        success = False
        
        try:
            if db_type == "SQLite":
                db_path = self.db_path_edit.text().strip()
                if not db_path:
                    QMessageBox.warning(self, "警告", "请选择SQLite数据库文件")
                    return
                success = self.db_connection.connect_sqlite(db_path)
            
            elif db_type == "MySQL":
                host = self.mysql_host_edit.text().strip()
                port = self.mysql_port_spin.value()
                user = self.mysql_user_edit.text().strip()
                password = self.mysql_pass_edit.text()
                database = self.mysql_db_edit.text().strip()
                
                if not all([host, user, database]):
                    QMessageBox.warning(self, "警告", "请填写完整的MySQL连接信息")
                    return
                
                success = self.db_connection.connect_mysql(
                    host, port, user, password, database
                )
            
            elif db_type == "PostgreSQL":
                host = self.pg_host_edit.text().strip()
                port = self.pg_port_spin.value()
                user = self.pg_user_edit.text().strip()
                password = self.pg_pass_edit.text()
                database = self.pg_db_edit.text().strip()
                
                if not all([host, user, database]):
                    QMessageBox.warning(self, "警告", "请填写完整的PostgreSQL连接信息")
                    return
                
                success = self.db_connection.connect_postgresql(
                    host, port, user, password, database
                )
            
            if success:
                self.db_metadata = DatabaseMetadata(self.db_connection)
                engine = self.db_connection.get_engine()
                db_type_lower = db_type.lower()
                self.sql_generator.set_engine(engine, db_type_lower)
                
                self._refresh_tables()
                
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)
                self.generate_btn.setEnabled(True)
                
                connection_info = self.db_connection.get_connection_info()
                self.status_bar.showMessage(f"已连接到 {connection_info['type']} 数据库")
                
                QMessageBox.information(self, "成功", "数据库连接成功！")
            else:
                QMessageBox.critical(self, "错误", "数据库连接失败，请检查连接参数")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接过程中发生错误: {str(e)}")
    
    def _disconnect_database(self):
        try:
            self.db_connection.close_connection()
            self.db_metadata = None
            self.sql_generator = SQLGenerator(llm_config_manager=self.llm_config_manager)
            
            self.tables_table.setRowCount(0)
            self.schema_text.clear()
            self.sql_text.clear()
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            self.results_text.clear()
            
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.generate_btn.setEnabled(False)
            self.execute_btn.setEnabled(False)
            
            self.status_bar.showMessage("就绪 - 请连接数据库")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"断开连接时发生错误: {str(e)}")
    
    def _refresh_tables(self):
        if not self.db_metadata:
            return
        
        try:
            tables = self.db_metadata.get_all_tables()
            self.tables_table.setRowCount(len(tables))
            
            for row, table_name in enumerate(tables):
                name_item = QTableWidgetItem(table_name)
                row_count = self.db_metadata.get_table_row_count(table_name)
                count_item = QTableWidgetItem(str(row_count))
                
                self.tables_table.setItem(row, 0, name_item)
                self.tables_table.setItem(row, 1, count_item)
            
            self.tables_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取表列表失败: {str(e)}")
    
    def _on_table_selected(self):
        selected_items = self.tables_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        table_name_item = self.tables_table.item(row, 0)
        if not table_name_item:
            return
        
        table_name = table_name_item.text()
        
        try:
            schema_text = self.db_metadata.get_table_schema_text(table_name)
            self.schema_text.setPlainText(schema_text)
            
        except Exception as e:
            self.schema_text.setPlainText(f"获取表结构失败: {str(e)}")
    
    def _generate_sql(self):
        natural_query = self.query_edit.toPlainText().strip()
        if not natural_query:
            QMessageBox.warning(self, "警告", "请输入自然语言查询")
            return
        
        if not self.db_metadata:
            QMessageBox.warning(self, "警告", "请先连接数据库")
            return
        
        try:
            table_schemas = self.db_metadata.get_all_schemas_text()
            
            tables = self.db_metadata.get_all_tables()
            sample_data = {}
            for table in tables[:3]:
                data = self.db_metadata.get_sample_data(table, limit=3)
                if data:
                    sample_data[table] = data
            
            connection_info = self.db_connection.get_connection_info()
            db_type = connection_info.get('type', 'sqlite')
            
            self.generate_btn.setEnabled(False)
            self.status_bar.showMessage("正在生成SQL...")
            
            self.sql_thread = SQLGenerationThread(
                self.sql_generator,
                natural_query,
                table_schemas,
                sample_data,
                db_type
            )
            self.sql_thread.finished_signal.connect(self._on_sql_generated)
            self.sql_thread.error_signal.connect(self._on_sql_error)
            self.sql_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成SQL时发生错误: {str(e)}")
            self.generate_btn.setEnabled(True)
    
    def _on_sql_generated(self, sql):
        self.sql_text.setPlainText(sql)
        self.execute_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.status_bar.showMessage("SQL生成完成")
    
    def _on_sql_error(self, error_msg):
        QMessageBox.critical(self, "错误", f"SQL生成失败: {error_msg}")
        self.generate_btn.setEnabled(True)
        self.status_bar.showMessage("SQL生成失败")
    
    def _execute_sql(self):
        sql = self.sql_text.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "警告", "没有可执行的SQL语句")
            return
        
        try:
            self.execute_btn.setEnabled(False)
            self.status_bar.showMessage("正在执行SQL...")
            
            self.exec_thread = SQLExecutionThread(self.sql_generator, sql)
            self.exec_thread.finished_signal.connect(self._on_execution_finished)
            self.exec_thread.error_signal.connect(self._on_execution_error)
            self.exec_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行SQL时发生错误: {str(e)}")
            self.execute_btn.setEnabled(True)
    
    def _on_execution_finished(self, result):
        try:
            if result.get('success'):
                columns = result.get('columns', [])
                rows = result.get('rows', [])
                row_count = result.get('row_count', 0)
                
                self.results_table.setRowCount(len(rows))
                self.results_table.setColumnCount(len(columns))
                self.results_table.setHorizontalHeaderLabels(columns)
                
                for row_idx, row_data in enumerate(rows):
                    for col_idx, col_name in enumerate(columns):
                        value = row_data.get(col_name, "")
                        item = QTableWidgetItem(str(value))
                        self.results_table.setItem(row_idx, col_idx, item)
                
                self.results_table.resizeColumnsToContents()
                
                import json
                self.results_text.setPlainText(json.dumps(rows, ensure_ascii=False, indent=2))
                
                self.status_bar.showMessage(f"执行成功，返回 {row_count} 行数据")
            else:
                error_msg = result.get('error', '未知错误')
                QMessageBox.critical(self, "执行失败", f"SQL执行失败: {error_msg}")
                self.status_bar.showMessage("SQL执行失败")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理结果时发生错误: {str(e)}")
        
        finally:
            self.execute_btn.setEnabled(True)
    
    def _on_execution_error(self, error_msg):
        QMessageBox.critical(self, "错误", f"执行过程中发生错误: {error_msg}")
        self.execute_btn.setEnabled(True)
        self.status_bar.showMessage("SQL执行失败")
    
    def closeEvent(self, event):
        try:
            if self.db_connection.is_connected():
                self.db_connection.close_connection()
        except:
            pass
        event.accept()

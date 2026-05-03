from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QLineEdit, QPushButton, QGroupBox, QFormLayout, QDoubleSpinBox,
    QSpinBox, QMessageBox, QListWidget, QListWidgetItem, QSplitter,
    QWidget, QTabWidget, QPlainTextEdit, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.text2sql.llm_config import (
    LLMConfig, LLMConfigManager, LLMPlatform,
    PRESET_MODELS, PLATFORM_BASE_URLS, PLATFORM_DISPLAY_NAMES
)


class LLMConfigDialog(QDialog):
    def __init__(self, parent=None, config_manager: LLMConfigManager = None):
        super().__init__(parent)
        self.setWindowTitle("大模型配置")
        self.setMinimumSize(800, 600)
        
        self.config_manager = config_manager or LLMConfigManager()
        self.current_config_name = self.config_manager.active_config_name
        
        self._init_ui()
        self._load_config_list()
    
    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        
        list_label = QLabel("配置列表:")
        left_layout.addWidget(list_label)
        
        self.config_list = QListWidget()
        self.config_list.setMaximumWidth(200)
        self.config_list.currentRowChanged.connect(self._on_config_selected)
        left_layout.addWidget(self.config_list, 1)
        
        list_btn_layout = QHBoxLayout()
        self.add_config_btn = QPushButton("新建")
        self.add_config_btn.clicked.connect(self._add_new_config)
        self.delete_config_btn = QPushButton("删除")
        self.delete_config_btn.clicked.connect(self._delete_config)
        self.set_active_btn = QPushButton("设为活动")
        self.set_active_btn.clicked.connect(self._set_as_active)
        
        list_btn_layout.addWidget(self.add_config_btn)
        list_btn_layout.addWidget(self.delete_config_btn)
        list_btn_layout.addWidget(self.set_active_btn)
        left_layout.addLayout(list_btn_layout)
        
        main_layout.addWidget(left_widget)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        
        self.config_tabs = QTabWidget()
        
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        platform_group = QGroupBox("平台设置")
        platform_layout = QFormLayout(platform_group)
        
        self.platform_combo = QComboBox()
        for platform in LLMPlatform:
            display_name = PLATFORM_DISPLAY_NAMES.get(platform, platform.value)
            self.platform_combo.addItem(display_name, platform.value)
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        platform_layout.addRow("平台类型:", self.platform_combo)
        
        self.preset_model_combo = QComboBox()
        self.preset_model_combo.setEditable(True)
        self.preset_model_combo.currentIndexChanged.connect(self._on_preset_model_changed)
        platform_layout.addRow("模型:", self.preset_model_combo)
        
        basic_layout.addWidget(platform_group)
        
        credentials_group = QGroupBox("凭证设置")
        credentials_layout = QFormLayout(credentials_group)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("输入API Key")
        credentials_layout.addRow("API Key:", self.api_key_edit)
        
        self.show_key_checkbox = QCheckBox("显示API Key")
        self.show_key_checkbox.stateChanged.connect(self._toggle_api_key_visibility)
        credentials_layout.addRow("", self.show_key_checkbox)
        
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("留空使用平台默认地址")
        credentials_layout.addRow("Base URL:", self.base_url_edit)
        
        basic_layout.addWidget(credentials_group)
        
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)
        
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.0)
        self.temp_spin.setDecimals(1)
        advanced_layout.addRow("Temperature:", self.temp_spin)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 128000)
        self.max_tokens_spin.setValue(4096)
        self.max_tokens_spin.setSingleStep(100)
        advanced_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(60)
        self.timeout_spin.setSingleStep(10)
        advanced_layout.addRow("超时(秒):", self.timeout_spin)
        
        basic_layout.addWidget(advanced_group)
        
        info_group = QGroupBox("配置信息")
        info_layout = QFormLayout(info_group)
        
        self.config_name_label = QLabel("-")
        info_layout.addRow("配置名称:", self.config_name_label)
        
        self.active_status_label = QLabel("-")
        info_layout.addRow("活动状态:", self.active_status_label)
        
        basic_layout.addWidget(info_group)
        basic_layout.addStretch()
        
        self.config_tabs.addTab(basic_tab, "基本设置")
        
        prompt_tab = QWidget()
        prompt_layout = QVBoxLayout(prompt_tab)
        
        prompt_label = QLabel("系统提示词模板 (用于SQL生成):")
        prompt_layout.addWidget(prompt_label)
        
        self.system_prompt_edit = QPlainTextEdit()
        self.system_prompt_edit.setPlaceholderText("输入系统提示词模板...")
        self.system_prompt_edit.setPlainText(
            "你是一个专业的SQL工程师，擅长将自然语言转换为SQL语句。"
            "特别注意：要根据查询语义选择正确的表，不要默认使用第一个表。"
        )
        prompt_layout.addWidget(self.system_prompt_edit, 1)
        
        example_label = QLabel("示例查询提示:")
        prompt_layout.addWidget(example_label)
        
        self.example_edit = QPlainTextEdit()
        self.example_edit.setReadOnly(True)
        self.example_edit.setPlainText(
            "查询'作者信息' -> SELECT * FROM authors\n"
            "查询'书籍信息' -> SELECT * FROM books\n"
            "查询'作者和他们的书籍' -> SELECT a.*, b.* FROM authors a JOIN books b ON a.id = b.author_id\n"
            "查询'员工数量' -> SELECT COUNT(*) FROM employees\n"
            "查询'每个部门的员工数量' -> SELECT department_id, COUNT(*) FROM employees GROUP BY department_id"
        )
        prompt_layout.addWidget(self.example_edit)
        
        self.config_tabs.addTab(prompt_tab, "提示词设置")
        
        right_layout.addWidget(self.config_tabs, 1)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self._save_current_config)
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._test_connection)
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.test_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        right_layout.addLayout(btn_layout)
        
        main_layout.addWidget(right_widget, 1)
    
    def _load_config_list(self):
        self.config_list.clear()
        config_names = self.config_manager.get_config_names()
        
        for name in config_names:
            item = QListWidgetItem(name)
            if name == self.config_manager.active_config_name:
                item.setText(f"{name} (活动)")
            self.config_list.addItem(item)
        
        if config_names:
            index = config_names.index(self.current_config_name)
            if index >= 0:
                self.config_list.setCurrentRow(index)
    
    def _on_config_selected(self, row):
        if row < 0:
            return
        
        config_names = self.config_manager.get_config_names()
        if row >= len(config_names):
            return
        
        config_name = config_names[row]
        self.current_config_name = config_name
        
        config = self.config_manager.get_config(config_name)
        if config:
            self._populate_form(config)
        
        self.config_name_label.setText(config_name)
        is_active = config_name == self.config_manager.active_config_name
        self.active_status_label.setText("是" if is_active else "否")
    
    def _populate_form(self, config: LLMConfig):
        platform_value = config.platform.value
        index = self.platform_combo.findData(platform_value)
        if index >= 0:
            self.platform_combo.setCurrentIndex(index)
        
        self._update_preset_models(config.platform)
        
        model_index = self.preset_model_combo.findText(config.model_name)
        if model_index >= 0:
            self.preset_model_combo.setCurrentIndex(model_index)
        else:
            self.preset_model_combo.setCurrentText(config.model_name)
        
        self.api_key_edit.setText(config.api_key)
        
        if config.base_url:
            self.base_url_edit.setText(config.base_url)
        else:
            default_url = PLATFORM_BASE_URLS.get(config.platform, "")
            self.base_url_edit.setPlaceholderText(default_url or "输入自定义Base URL")
        
        self.temp_spin.setValue(config.temperature)
        self.max_tokens_spin.setValue(config.max_tokens)
        self.timeout_spin.setValue(config.timeout)
    
    def _on_platform_changed(self, index):
        platform_value = self.platform_combo.currentData()
        if platform_value:
            platform = LLMPlatform(platform_value)
            self._update_preset_models(platform)
            
            default_url = PLATFORM_BASE_URLS.get(platform, "")
            if default_url:
                self.base_url_edit.setPlaceholderText(default_url)
            else:
                self.base_url_edit.setPlaceholderText("输入自定义Base URL")
    
    def _update_preset_models(self, platform: LLMPlatform):
        self.preset_model_combo.clear()
        
        presets = PRESET_MODELS.get(platform, [])
        for preset in presets:
            self.preset_model_combo.addItem(preset['name'])
        
        if presets:
            self.preset_model_combo.setCurrentIndex(0)
    
    def _on_preset_model_changed(self, index):
        pass
    
    def _toggle_api_key_visibility(self, state):
        if state == Qt.CheckState.Checked.value:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _add_new_config(self):
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "新建配置", "输入配置名称:")
        if ok and name.strip():
            name = name.strip()
            if self.config_manager.get_config(name):
                QMessageBox.warning(self, "警告", f"配置 '{name}' 已存在")
                return
            
            new_config = LLMConfig()
            self.config_manager.add_config(name, new_config)
            self._load_config_list()
            
            config_names = self.config_manager.get_config_names()
            index = config_names.index(name)
            self.config_list.setCurrentRow(index)
            
            QMessageBox.information(self, "成功", f"配置 '{name}' 已创建")
    
    def _delete_config(self):
        current_row = self.config_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的配置")
            return
        
        config_names = self.config_manager.get_config_names()
        if current_row >= len(config_names):
            return
        
        config_name = config_names[current_row]
        
        if config_name == "default":
            QMessageBox.warning(self, "警告", "不能删除默认配置")
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除配置 '{config_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.delete_config(config_name)
            self._load_config_list()
            QMessageBox.information(self, "成功", f"配置 '{config_name}' 已删除")
    
    def _set_as_active(self):
        current_row = self.config_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要设为活动的配置")
            return
        
        config_names = self.config_manager.get_config_names()
        if current_row >= len(config_names):
            return
        
        config_name = config_names[current_row]
        
        if config_name == self.config_manager.active_config_name:
            QMessageBox.information(self, "提示", "该配置已经是活动配置")
            return
        
        self.config_manager.set_active_config(config_name)
        self._load_config_list()
        
        QMessageBox.information(self, "成功", f"配置 '{config_name}' 已设为活动配置")
    
    def _save_current_config(self):
        if not self.current_config_name:
            QMessageBox.warning(self, "警告", "请先选择或创建一个配置")
            return
        
        platform_value = self.platform_combo.currentData()
        platform = LLMPlatform(platform_value)
        
        config = LLMConfig(
            platform=platform,
            api_key=self.api_key_edit.text().strip(),
            model_name=self.preset_model_combo.currentText().strip(),
            base_url=self.base_url_edit.text().strip() or None,
            temperature=self.temp_spin.value(),
            max_tokens=self.max_tokens_spin.value(),
            timeout=self.timeout_spin.value()
        )
        
        self.config_manager.update_config(self.current_config_name, config)
        
        QMessageBox.information(self, "成功", "配置已保存")
    
    def _test_connection(self):
        if not self.current_config_name:
            QMessageBox.warning(self, "警告", "请先选择一个配置")
            return
        
        config = self.config_manager.get_config(self.current_config_name)
        if not config:
            QMessageBox.warning(self, "警告", "无法获取配置")
            return
        
        if not config.api_key or not config.api_key.strip():
            QMessageBox.warning(self, "警告", "请先配置API Key")
            return
        
        from PyQt6.QtWidgets import QProgressDialog
        from PyQt6.QtCore import QTimer
        
        progress = QProgressDialog("正在测试连接...", "取消", 0, 0, self)
        progress.setWindowTitle("测试连接")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        QTimer.singleShot(100, lambda: self._do_test_connection(config, progress))
    
    def _do_test_connection(self, config: LLMConfig, progress):
        try:
            from src.text2sql.llm_config import create_llm_client
            from langchain_core.messages import HumanMessage
            
            llm = create_llm_client(config)
            
            response = llm.invoke([HumanMessage(content="请回复'连接成功'")])
            result = response.content
            
            progress.close()
            
            if "成功" in result or "success" in result.lower():
                QMessageBox.information(self, "成功", f"连接测试成功！\n\n模型回复: {result}")
            else:
                QMessageBox.information(self, "信息", f"连接可用\n\n模型回复: {result}")
                
        except ImportError as e:
            progress.close()
            QMessageBox.critical(self, "错误", f"缺少依赖库: {str(e)}\n请安装: pip install langchain-openai")
        except Exception as e:
            progress.close()
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                QMessageBox.critical(self, "认证失败", 
                    f"API Key认证失败，请检查:\n1. API Key是否正确\n2. 账户是否有余额\n3. 平台是否支持该模型\n\n错误详情: {error_msg}")
            elif "404" in error_msg or "not found" in error_msg.lower():
                QMessageBox.critical(self, "模型不存在", 
                    f"模型不存在，请检查:\n1. 模型名称是否正确\n2. 该平台是否支持此模型\n\n错误详情: {error_msg}")
            else:
                QMessageBox.critical(self, "连接失败", f"连接测试失败:\n{error_msg}")
    
    def get_config_manager(self) -> LLMConfigManager:
        return self.config_manager

import os
import json
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QPlainTextEdit, QScrollArea,
    QFrame, QGroupBox, QSpinBox, QDoubleSpinBox, QGridLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from qfluentwidgets import (
    PushButton, ComboBox, LineEdit, SpinBox, DoubleSpinBox,
    MessageBox, InfoBar, InfoBarPosition, SearchLineEdit,
    FluentIcon as FIF, TableWidget, RoundMenu, Action,
    TransparentToolButton, ToolButton, TextEdit, PlainTextEdit,
    ScrollArea, ExpandLayout, CardWidget, SimpleCardWidget,
    Slider, PrimaryPushButton, TitleLabel, BodyLabel
)

class FormulaManagementView(QWidget):
    """部门职级计算公式管理界面"""
    
    def __init__(self, score_db, parent=None):
        super().__init__(parent)
        self.score_db = score_db
        
        # 初始化界面
        self.initUI()
        
    def initUI(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 顶部控制区域
        top_layout = QHBoxLayout()
        
        # 添加部门选择下拉框
        self.department_combo = ComboBox(self)
        self.department_combo.setPlaceholderText("选择部门")
        self.load_departments()
        
        self.department_combo.setMinimumWidth(150)
        self.department_combo.currentIndexChanged.connect(self.load_department_formula)
        top_layout.addWidget(QLabel("部门:"))
        top_layout.addWidget(self.department_combo)
        
        top_layout.addStretch(1)
        
        # 保存按钮
        self.save_button = PushButton("保存公式", self, FIF.SAVE)
        self.save_button.clicked.connect(self.save_formula)
        top_layout.addWidget(self.save_button)
        
        # 测试按钮
        self.test_button = PushButton("测试公式", self, FIF.SEARCH)
        self.test_button.clicked.connect(self.test_formula)
        top_layout.addWidget(self.test_button)
        
        main_layout.addLayout(top_layout)
        
        # 添加选项卡界面
        self.tabs = QTabWidget(self)
        self.tabs.setDocumentMode(True)
        
        # 公式定义选项卡
        self.formula_tab = QWidget()
        self.formula_layout = QVBoxLayout(self.formula_tab)
        self.setup_formula_tab()
        self.tabs.addTab(self.formula_tab, "公式设置")
        
        # 公式说明选项卡
        self.description_tab = QWidget()
        self.description_layout = QVBoxLayout(self.description_tab)
        self.setup_description_tab()
        self.tabs.addTab(self.description_tab, "公式说明")
        
        # 添加选项卡
        main_layout.addWidget(self.tabs)
    
    def setup_formula_tab(self):
        """设置公式定义选项卡"""
        # 说明标签
        hint_label = QLabel("请通过添加职级阈值，设置员工总分与职级之间的对应关系")
        hint_label.setWordWrap(True)
        self.formula_layout.addWidget(hint_label)
        
        # 职级阈值卡片
        self.thresholds_card = SimpleCardWidget(self.formula_tab)
        self.thresholds_layout = QVBoxLayout(self.thresholds_card)
        
        # 职级阈值表格
        self.thresholds_table = TableWidget(self.thresholds_card)
        self.thresholds_table.setColumnCount(4)
        self.thresholds_table.setHorizontalHeaderLabels(['职级', '最低分数', '最高分数', '操作'])
        self.thresholds_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.thresholds_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.thresholds_layout.addWidget(self.thresholds_table)
        
        # 添加阈值按钮
        add_threshold_button = PushButton("添加职级阈值", self.thresholds_card, FIF.ADD)
        add_threshold_button.clicked.connect(self.add_threshold)
        self.thresholds_layout.addWidget(add_threshold_button)
        
        self.formula_layout.addWidget(self.thresholds_card)
        
        # 高级设置卡片
        self.advanced_card = SimpleCardWidget(self.formula_tab)
        self.advanced_layout = QVBoxLayout(self.advanced_card)
        
        # 高级公式设置（JSON编辑器）
        self.advanced_label = QLabel("高级公式设置 (JSON格式):")
        self.advanced_layout.addWidget(self.advanced_label)
        
        self.formula_json_edit = PlainTextEdit(self.advanced_card)
        self.formula_json_edit.setPlaceholderText("{\n  \"grade_thresholds\": [\n    {\"grade\": \"G1\", \"min_score\": 0, \"max_score\": 60},\n    {\"grade\": \"G2\", \"min_score\": 61, \"max_score\": 80},\n    {\"grade\": \"G3\", \"min_score\": 81, \"max_score\": 100}\n  ]\n}")
        self.formula_json_edit.setMinimumHeight(200)
        self.advanced_layout.addWidget(self.formula_json_edit)
        
        # 同步按钮
        sync_layout = QHBoxLayout()
        
        sync_to_table_button = PushButton("从JSON同步到表格", self.advanced_card)
        sync_to_table_button.clicked.connect(self.sync_json_to_table)
        sync_layout.addWidget(sync_to_table_button)
        
        sync_to_json_button = PushButton("从表格同步到JSON", self.advanced_card)
        sync_to_json_button.clicked.connect(self.sync_table_to_json)
        sync_layout.addWidget(sync_to_json_button)
        
        self.advanced_layout.addLayout(sync_layout)
        
        self.formula_layout.addWidget(self.advanced_card)
    
    def setup_description_tab(self):
        """设置公式说明选项卡"""
        # 说明编辑器
        description_label = QLabel("公式说明 (提供详细的计算规则说明，帮助其他用户理解):")
        self.description_layout.addWidget(description_label)
        
        self.description_edit = TextEdit(self.description_tab)
        self.description_edit.setMinimumHeight(300)
        self.description_layout.addWidget(self.description_edit)
    
    def load_departments(self):
        """加载部门列表"""
        departments = self.score_db.get_all_departments()
        for dept in departments:
            self.department_combo.addItem(dept, dept)
    
    def load_department_formula(self):
        """加载选定部门的职级计算公式"""
        department = self.department_combo.currentData()
        if not department:
            return
        
        # 获取部门公式
        formula_data = self.score_db.get_department_formula(department)
        
        if formula_data:
            # 填充表格
            self.fill_thresholds_table(formula_data['formula'])
            
            # 设置JSON编辑器
            try:
                json_str = json.dumps(formula_data['formula'], indent=2, ensure_ascii=False)
                self.formula_json_edit.setPlainText(json_str)
            except Exception as e:
                print(f"转换公式为JSON失败: {e}")
            
            # 设置说明
            self.description_edit.setText(formula_data['description'] or "")
        else:
            # 清空表格和编辑器
            self.thresholds_table.setRowCount(0)
            self.formula_json_edit.setPlainText("")
            self.description_edit.setText("")
    
    def fill_thresholds_table(self, formula):
        """填充职级阈值表格"""
        self.thresholds_table.setRowCount(0)  # 清空表格
        
        if not formula or 'grade_thresholds' not in formula:
            return
        
        thresholds = formula['grade_thresholds']
        
        for row, threshold in enumerate(thresholds):
            self.thresholds_table.insertRow(row)
            
            # 设置职级
            grade_item = QTableWidgetItem(threshold['grade'])
            self.thresholds_table.setItem(row, 0, grade_item)
            
            # 设置最低分数
            min_score_item = QTableWidgetItem(str(threshold['min_score']))
            self.thresholds_table.setItem(row, 1, min_score_item)
            
            # 设置最高分数
            max_score_item = QTableWidgetItem(str(threshold['max_score']))
            self.thresholds_table.setItem(row, 2, max_score_item)
            
            # 设置操作列
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            edit_button = TransparentToolButton(FIF.EDIT)
            edit_button.setFixedSize(QSize(30, 30))
            edit_button.setToolTip("编辑")
            edit_button.clicked.connect(lambda _, r=row: self.edit_threshold(r))
            
            delete_button = TransparentToolButton(FIF.DELETE)
            delete_button.setFixedSize(QSize(30, 30))
            delete_button.setToolTip("删除")
            delete_button.clicked.connect(lambda _, r=row: self.delete_threshold(r))
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            actions_layout.addStretch(1)
            
            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            
            self.thresholds_table.setCellWidget(row, 3, actions_widget)
    
    def add_threshold(self):
        """添加职级阈值"""
        dialog = ThresholdDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            threshold_data = dialog.get_threshold_data()
            
            row = self.thresholds_table.rowCount()
            self.thresholds_table.insertRow(row)
            
            # 设置数据
            self.thresholds_table.setItem(row, 0, QTableWidgetItem(threshold_data['grade']))
            self.thresholds_table.setItem(row, 1, QTableWidgetItem(str(threshold_data['min_score'])))
            self.thresholds_table.setItem(row, 2, QTableWidgetItem(str(threshold_data['max_score'])))
            
            # 设置操作列
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            edit_button = TransparentToolButton(FIF.EDIT)
            edit_button.setFixedSize(QSize(30, 30))
            edit_button.setToolTip("编辑")
            edit_button.clicked.connect(lambda _, r=row: self.edit_threshold(r))
            
            delete_button = TransparentToolButton(FIF.DELETE)
            delete_button.setFixedSize(QSize(30, 30))
            delete_button.setToolTip("删除")
            delete_button.clicked.connect(lambda _, r=row: self.delete_threshold(r))
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            actions_layout.addStretch(1)
            
            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            
            self.thresholds_table.setCellWidget(row, 3, actions_widget)
            
            # 同步到JSON
            self.sync_table_to_json()
    
    def edit_threshold(self, row):
        """编辑职级阈值"""
        grade = self.thresholds_table.item(row, 0).text()
        min_score = float(self.thresholds_table.item(row, 1).text())
        max_score = float(self.thresholds_table.item(row, 2).text())
        
        threshold_data = {
            'grade': grade,
            'min_score': min_score,
            'max_score': max_score
        }
        
        dialog = ThresholdDialog(self, threshold_data)
        if dialog.exec_() == QDialog.Accepted:
            new_threshold_data = dialog.get_threshold_data()
            
            # 更新表格
            self.thresholds_table.setItem(row, 0, QTableWidgetItem(new_threshold_data['grade']))
            self.thresholds_table.setItem(row, 1, QTableWidgetItem(str(new_threshold_data['min_score'])))
            self.thresholds_table.setItem(row, 2, QTableWidgetItem(str(new_threshold_data['max_score'])))
            
            # 同步到JSON
            self.sync_table_to_json()
    
    def delete_threshold(self, row):
        """删除职级阈值"""
        # 弹出确认对话框
        dialog = MessageBox(
            '确认删除',
            f"确定要删除此职级阈值吗？",
            self
        )
        
        dialog.yesButton.setText('确认删除')
        dialog.cancelButton.setText('取消')
        
        if dialog.exec():
            self.thresholds_table.removeRow(row)
            
            # 同步到JSON
            self.sync_table_to_json()
    
    def sync_table_to_json(self):
        """从表格同步数据到JSON编辑器"""
        thresholds = []
        
        for row in range(self.thresholds_table.rowCount()):
            threshold = {
                'grade': self.thresholds_table.item(row, 0).text(),
                'min_score': float(self.thresholds_table.item(row, 1).text()),
                'max_score': float(self.thresholds_table.item(row, 2).text())
            }
            thresholds.append(threshold)
        
        formula = {
            'grade_thresholds': thresholds
        }
        
        try:
            json_str = json.dumps(formula, indent=2, ensure_ascii=False)
            self.formula_json_edit.setPlainText(json_str)
        except Exception as e:
            InfoBar.error(
                title='同步失败',
                content=f"转换为JSON失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def sync_json_to_table(self):
        """从JSON编辑器同步数据到表格"""
        json_text = self.formula_json_edit.toPlainText()
        
        try:
            formula = json.loads(json_text)
            self.fill_thresholds_table(formula)
        except Exception as e:
            InfoBar.error(
                title='同步失败',
                content=f"解析JSON失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def save_formula(self):
        """保存公式"""
        department = self.department_combo.currentData()
        
        if not department:
            InfoBar.error(
                title='保存失败',
                content="请选择部门",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 从JSON编辑器获取公式
        json_text = self.formula_json_edit.toPlainText()
        description = self.description_edit.toPlainText()
        
        try:
            formula = json.loads(json_text)
            
            # 验证公式结构
            if 'grade_thresholds' not in formula or not isinstance(formula['grade_thresholds'], list):
                raise ValueError("公式格式错误: 缺少'grade_thresholds'数组")
                
            for threshold in formula['grade_thresholds']:
                if not all(k in threshold for k in ['grade', 'min_score', 'max_score']):
                    raise ValueError("职级阈值格式错误: 缺少必要的字段(grade, min_score, max_score)")
            
            # 保存公式
            success = self.score_db.save_department_formula(department, formula, description)
            
            if success:
                InfoBar.success(
                    title='保存成功',
                    content=f"已成功保存 {department} 部门的职级计算公式",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title='保存失败',
                    content="保存公式时出现错误",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                
        except Exception as e:
            InfoBar.error(
                title='保存失败',
                content=f"公式格式错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def test_formula(self):
        """测试公式"""
        department = self.department_combo.currentData()
        
        if not department:
            InfoBar.error(
                title='测试失败',
                content="请选择部门",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
            
        # 获取公式
        json_text = self.formula_json_edit.toPlainText()
        
        try:
            formula = json.loads(json_text)
            
            # 打开测试对话框
            dialog = FormulaTestDialog(self, formula)
            dialog.exec_()
            
        except Exception as e:
            InfoBar.error(
                title='测试失败',
                content=f"公式格式错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )


class ThresholdDialog(QDialog):
    """职级阈值编辑对话框"""
    
    def __init__(self, parent=None, threshold_data=None):
        super().__init__(parent)
        self.threshold_data = threshold_data
        self.is_edit_mode = threshold_data is not None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 设置窗口标题
        title = "编辑职级阈值" if self.is_edit_mode else "添加职级阈值"
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 职级
        self.grade_edit = LineEdit(self)
        self.grade_edit.setClearButtonEnabled(True)
        self.grade_edit.setPlaceholderText("如 G1, G2, G3, G4A 等")
        form_layout.addRow("职级:", self.grade_edit)
        
        # 最低分数
        self.min_score_spin = DoubleSpinBox(self)
        self.min_score_spin.setRange(0, 1000)
        self.min_score_spin.setSingleStep(1)
        self.min_score_spin.setValue(0)
        form_layout.addRow("最低分数:", self.min_score_spin)
        
        # 最高分数
        self.max_score_spin = DoubleSpinBox(self)
        self.max_score_spin.setRange(0, 1000)
        self.max_score_spin.setSingleStep(1)
        self.max_score_spin.setValue(100)
        form_layout.addRow("最高分数:", self.max_score_spin)
        
        layout.addLayout(form_layout)
        
        # 添加提示文本
        hint_label = QLabel("注意: 请确保不同职级的分数范围不重叠，否则可能导致预测结果不准确。")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.cancel_button = PushButton("取消", self)
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = PushButton("保存", self, FIF.SAVE)
        self.save_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # 如果是编辑模式，填充现有数据
        if self.is_edit_mode:
            self.fill_form_data()
    
    def fill_form_data(self):
        """填充表单数据（编辑模式）"""
        if self.threshold_data:
            self.grade_edit.setText(self.threshold_data['grade'])
            self.min_score_spin.setValue(self.threshold_data['min_score'])
            self.max_score_spin.setValue(self.threshold_data['max_score'])
    
    def get_threshold_data(self):
        """获取职级阈值数据"""
        return {
            'grade': self.grade_edit.text(),
            'min_score': self.min_score_spin.value(),
            'max_score': self.max_score_spin.value()
        }


class FormulaTestDialog(QDialog):
    """公式测试对话框"""
    
    def __init__(self, parent=None, formula=None):
        super().__init__(parent)
        self.formula = formula
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("测试职级计算公式")
        self.setMinimumWidth(400)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 输入表单
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 当前职级
        self.current_grade_edit = LineEdit(self)
        self.current_grade_edit.setText("G2")  # 默认值
        form_layout.addRow("当前职级:", self.current_grade_edit)
        
        # 总分
        self.total_score_spin = DoubleSpinBox(self)
        self.total_score_spin.setRange(0, 1000)
        self.total_score_spin.setSingleStep(1)
        self.total_score_spin.setValue(75)  # 默认值
        form_layout.addRow("考核总分:", self.total_score_spin)
        
        layout.addLayout(form_layout)
        
        # 添加计算按钮
        self.calculate_button = PrimaryPushButton("计算预测职级", self)
        self.calculate_button.clicked.connect(self.calculate_grade)
        layout.addWidget(self.calculate_button)
        
        # 结果区域
        result_group = QGroupBox("计算结果", self)
        result_layout = QVBoxLayout(result_group)
        
        self.result_label = TitleLabel("", self)
        self.result_label.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(self.result_label)
        
        layout.addWidget(result_group)
        
        # 公式预览
        formula_group = QGroupBox("公式预览", self)
        formula_layout = QVBoxLayout(formula_group)
        
        self.formula_text = PlainTextEdit(formula_group)
        self.formula_text.setReadOnly(True)
        
        try:
            json_str = json.dumps(self.formula, indent=2, ensure_ascii=False)
            self.formula_text.setPlainText(json_str)
        except Exception:
            self.formula_text.setPlainText("公式解析错误")
            
        formula_layout.addWidget(self.formula_text)
        
        layout.addWidget(formula_group)
        
        # 关闭按钮
        self.close_button = PushButton("关闭", self)
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)
    
    def calculate_grade(self):
        """计算预测职级"""
        current_grade = self.current_grade_edit.text().strip()
        total_score = self.total_score_spin.value()
        
        if not current_grade:
            InfoBar.error(
                title='输入错误',
                content="请输入当前职级",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 应用公式
        predicted_grade = self._apply_formula(total_score, current_grade)
        
        # 显示结果
        result_text = f"预测职级: {predicted_grade}"
        self.result_label.setText(result_text)
        
        # 添加结果说明
        if predicted_grade == current_grade:
            result_hint = f"当前职级: {current_grade} → 预测职级: {predicted_grade} (保持不变)"
        elif self._is_promotion(current_grade, predicted_grade):
            result_hint = f"当前职级: {current_grade} → 预测职级: {predicted_grade} (晋升)"
        else:
            result_hint = f"当前职级: {current_grade} → 预测职级: {predicted_grade} (降级)"
            
        InfoBar.success(
            title='计算完成',
            content=result_hint,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )
    
    def _apply_formula(self, total_score, current_grade):
        """应用公式计算预测职级"""
        if 'grade_thresholds' in self.formula:
            thresholds = self.formula['grade_thresholds']
            for threshold in thresholds:
                if total_score >= threshold['min_score'] and total_score <= threshold['max_score']:
                    return threshold['grade']
        
        # 如果没有匹配的阈值，返回当前职级
        return current_grade
    
    def _is_promotion(self, current_grade, predicted_grade):
        """判断是否为晋升"""
        # 简单判断常见职级格式
        # G1 < G2 < G3 < G4A < G4B < G5
        grades = {
            'G1': 1, 'G2': 2, 'G3': 3, 'G4A': 4, 'G4B': 5, 'G5': 6,
            'g1': 1, 'g2': 2, 'g3': 3, 'g4a': 4, 'g4b': 5, 'g5': 6
        }
        
        current_value = grades.get(current_grade, 0)
        predicted_value = grades.get(predicted_grade, 0)
        
        return predicted_value > current_value 
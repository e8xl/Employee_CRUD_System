import os
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFileDialog, QMessageBox, QLineEdit, QAbstractItemView,
    QDialog, QFormLayout, QDoubleSpinBox, QSpinBox
)
from qfluentwidgets import (
    PushButton, ComboBox, LineEdit, SpinBox, DoubleSpinBox,
    MessageBox, InfoBar, InfoBarPosition, SearchLineEdit,
    FluentIcon as FIF, TableWidget, RoundMenu, Action,
    TransparentToolButton, ToolButton
)

class AssessmentItemsView(QWidget):
    """考核项目管理界面"""
    
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
        main_layout.setSpacing(10)
        
        # 顶部控制区域
        top_layout = QHBoxLayout()
        
        # 添加部门筛选下拉框
        self.department_combo = ComboBox(self)
        self.department_combo.setPlaceholderText("选择部门")
        self.department_combo.addItem("全部部门", "all")
        self.load_departments()
        
        self.department_combo.setMinimumWidth(150)
        self.department_combo.currentIndexChanged.connect(self.filter_items)
        top_layout.addWidget(QLabel("部门:"))
        top_layout.addWidget(self.department_combo)
        
        # 添加搜索框
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("搜索考核项目")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(250)
        self.search_edit.textChanged.connect(self.filter_items)
        top_layout.addWidget(self.search_edit)
        
        top_layout.addStretch(1)
        
        # 添加按钮区域
        self.add_button = PushButton("添加项目", self, FIF.ADD)
        self.add_button.clicked.connect(self.add_item)
        top_layout.addWidget(self.add_button)
        
        self.import_button = PushButton("导入", self, FIF.DOWNLOAD)
        self.import_button.clicked.connect(self.import_items)
        top_layout.addWidget(self.import_button)
        
        self.export_button = PushButton("导出", self, FIF.SAVE)
        self.export_button.clicked.connect(self.export_items)
        top_layout.addWidget(self.export_button)
        
        main_layout.addLayout(top_layout)
        
        # 创建表格
        self.table = TableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', '部门', '考核项目', '权重', '满分', '操作'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止直接编辑表格
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 整行选择
        
        main_layout.addWidget(self.table)
        
        # 加载考核项目数据
        self.load_items()
    
    def load_departments(self):
        """加载部门列表"""
        departments = self.score_db.get_all_departments()
        for dept in departments:
            self.department_combo.addItem(dept, dept)
    
    def load_items(self):
        """加载考核项目数据"""
        items = self.score_db.get_all_assessment_items()
        self.populate_table(items)
    
    def filter_items(self):
        """根据筛选条件过滤考核项目"""
        department = self.department_combo.currentData()
        search_text = self.search_edit.text().strip().lower()
        
        # 根据部门筛选
        if department == "all":
            items = self.score_db.get_all_assessment_items()
        else:
            items = self.score_db.get_all_assessment_items(department)
        
        # 根据搜索文本筛选
        if search_text:
            filtered_items = []
            for item in items:
                if (search_text in item['department'].lower() or 
                    search_text in item['assessment_name'].lower()):
                    filtered_items.append(item)
            items = filtered_items
        
        self.populate_table(items)
    
    def populate_table(self, items):
        """填充表格数据"""
        self.table.setRowCount(0)  # 清空表格
        
        for row, item in enumerate(items):
            self.table.insertRow(row)
            
            # 设置ID列
            id_item = QTableWidgetItem(str(item['id']))
            self.table.setItem(row, 0, id_item)
            
            # 设置部门列
            dept_item = QTableWidgetItem(item['department'])
            self.table.setItem(row, 1, dept_item)
            
            # 设置考核项目名称列
            name_item = QTableWidgetItem(item['assessment_name'])
            self.table.setItem(row, 2, name_item)
            
            # 设置权重列
            weight_item = QTableWidgetItem(str(item['weight']))
            self.table.setItem(row, 3, weight_item)
            
            # 设置满分列
            max_score_item = QTableWidgetItem(str(item['max_score']))
            self.table.setItem(row, 4, max_score_item)
            
            # 设置操作列
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            edit_button = TransparentToolButton(FIF.EDIT)
            edit_button.setFixedSize(QSize(30, 30))
            edit_button.setToolTip("编辑")
            edit_button.clicked.connect(lambda _, i=item['id']: self.edit_item(i))
            
            delete_button = TransparentToolButton(FIF.DELETE)
            delete_button.setFixedSize(QSize(30, 30))
            delete_button.setToolTip("删除")
            delete_button.clicked.connect(lambda _, i=item['id']: self.delete_item(i))
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            actions_layout.addStretch(1)
            
            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            
            self.table.setCellWidget(row, 5, actions_widget)
    
    def add_item(self):
        """添加考核项目"""
        dialog = AssessmentItemDialog(self, self.score_db)
        if dialog.exec_() == QDialog.Accepted:
            self.load_items()
    
    def edit_item(self, item_id):
        """编辑考核项目"""
        # 先获取考核项目信息
        all_items = self.score_db.get_all_assessment_items()
        item_data = None
        
        for item in all_items:
            if item['id'] == item_id:
                item_data = item
                break
        
        if item_data:
            dialog = AssessmentItemDialog(self, self.score_db, item_data)
            if dialog.exec_() == QDialog.Accepted:
                self.load_items()
    
    def delete_item(self, item_id):
        """删除考核项目"""
        # 先获取考核项目信息
        all_items = self.score_db.get_all_assessment_items()
        item_data = None
        
        for item in all_items:
            if item['id'] == item_id:
                item_data = item
                break
        
        if item_data:
            # 弹出确认对话框
            dialog = MessageBox(
                '确认删除',
                f"确定要删除考核项目 '{item_data['assessment_name']}' 吗？\n此操作无法撤销，相关的考核成绩也将被删除。",
                self
            )
            
            # 添加确认和取消按钮
            dialog.yesButton.setText('确认删除')
            dialog.cancelButton.setText('取消')
            
            if dialog.exec():
                # 执行删除操作
                success = self.score_db.delete_assessment_item(item_id)
                
                if success:
                    InfoBar.success(
                        title='删除成功',
                        content=f"已成功删除考核项目 '{item_data['assessment_name']}'",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    self.load_items()
                else:
                    InfoBar.error(
                        title='删除失败',
                        content="删除考核项目时出现错误",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
    
    def import_items(self):
        """导入考核项目"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "", "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
            
        result = self.score_db.import_assessment_items(file_path)
        
        if result and result.get('success'):
            InfoBar.success(
                title='导入成功',
                content=f"成功导入考核项目: 新增 {result.get('added')} 项，更新 {result.get('updated')} 项",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self.load_items()
        else:
            InfoBar.error(
                title='导入失败',
                content="导入考核项目时出现错误",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def export_items(self):
        """导出考核项目"""
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
            
        try:
            # 获取考核项目数据
            department = self.department_combo.currentData()
            if department == "all":
                items = self.score_db.get_all_assessment_items()
            else:
                items = self.score_db.get_all_assessment_items(department)
            
            # 转换为DataFrame并导出
            import pandas as pd
            df = pd.DataFrame(items)
            
            # 只保留需要的列
            columns_to_export = ['department', 'assessment_name', 'weight', 'max_score']
            df = df[columns_to_export]
            
            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            elif file_path.endswith('.csv'):
                df.to_csv(file_path, index=False, encoding='utf-8')
            else:
                # 默认添加.xlsx后缀
                file_path += '.xlsx'
                df.to_excel(file_path, index=False)
            
            InfoBar.success(
                title='导出成功',
                content=f"已成功导出考核项目到 {file_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            InfoBar.error(
                title='导出失败',
                content=f"导出考核项目时出现错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )


class AssessmentItemDialog(QDialog):
    """考核项目添加/编辑对话框"""
    
    def __init__(self, parent=None, score_db=None, item_data=None):
        super().__init__(parent)
        self.score_db = score_db
        self.item_data = item_data  # 如果是编辑模式，则传入item_data
        self.is_edit_mode = item_data is not None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 设置窗口标题
        title = "编辑考核项目" if self.is_edit_mode else "添加考核项目"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 部门选择框
        self.department_combo = ComboBox(self)
        self.department_combo.setPlaceholderText("选择部门")
        self.load_departments()
        form_layout.addRow("部门:", self.department_combo)
        
        # 考核项目名称
        self.name_edit = LineEdit(self)
        self.name_edit.setClearButtonEnabled(True)
        form_layout.addRow("考核项目名称:", self.name_edit)
        
        # 权重
        self.weight_spin = DoubleSpinBox(self)
        self.weight_spin.setRange(0.1, 10.0)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setValue(1.0)
        form_layout.addRow("权重:", self.weight_spin)
        
        # 满分值
        self.max_score_spin = DoubleSpinBox(self)
        self.max_score_spin.setRange(1, 1000)
        self.max_score_spin.setSingleStep(1)
        self.max_score_spin.setValue(100.0)
        form_layout.addRow("满分值:", self.max_score_spin)
        
        layout.addLayout(form_layout)
        
        # 添加提示文本
        hint_label = QLabel("注意: 权重表示考核项目在总分中的相对重要性，满分值表示该项目的最高分值。")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.cancel_button = PushButton("取消", self)
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = PushButton("保存", self, FIF.SAVE)
        self.save_button.clicked.connect(self.save_item)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # 如果是编辑模式，填充现有数据
        if self.is_edit_mode:
            self.fill_form_data()
    
    def load_departments(self):
        """加载部门列表"""
        departments = self.score_db.get_all_departments()
        for dept in departments:
            self.department_combo.addItem(dept, dept)
    
    def fill_form_data(self):
        """填充表单数据（编辑模式）"""
        if self.item_data:
            # 设置部门
            index = self.department_combo.findData(self.item_data['department'])
            if index >= 0:
                self.department_combo.setCurrentIndex(index)
            
            # 设置其他字段
            self.name_edit.setText(self.item_data['assessment_name'])
            self.weight_spin.setValue(self.item_data['weight'])
            self.max_score_spin.setValue(self.item_data['max_score'])
    
    def save_item(self):
        """保存考核项目"""
        # 验证表单
        department = self.department_combo.currentData()
        name = self.name_edit.text().strip()
        weight = self.weight_spin.value()
        max_score = self.max_score_spin.value()
        
        if not department:
            InfoBar.error(
                title='验证失败',
                content="请选择部门",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
            
        if not name:
            InfoBar.error(
                title='验证失败',
                content="请输入考核项目名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 准备数据
        item_data = {
            'department': department,
            'assessment_name': name,
            'weight': weight,
            'max_score': max_score
        }
        
        # 保存数据
        if self.is_edit_mode:
            # 更新项目
            success = self.score_db.update_assessment_item(self.item_data['id'], item_data)
            message = "更新考核项目成功" if success else "更新考核项目失败"
        else:
            # 添加新项目
            result = self.score_db.add_assessment_item(item_data)
            success = result is not None
            message = "添加考核项目成功" if success else "添加考核项目失败"
        
        if success:
            InfoBar.success(
                title='成功',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            self.accept()  # 关闭对话框
        else:
            InfoBar.error(
                title='失败',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            ) 
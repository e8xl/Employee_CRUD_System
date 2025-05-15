from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QTextEdit, QDialog, QDialogButtonBox,
    QComboBox, QGroupBox
)
from qfluentwidgets import (
    LineEdit, ComboBox, TextEdit, PrimaryPushButton, 
    PushButton, CardWidget, FluentIcon, InfoBar,
    InfoBarPosition, setTheme, Theme, MessageBox
)

class EmployeeDetailView(QDialog):
    """员工详情视图，用于查看和编辑员工信息"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent = parent
        self.employee_id = None
        self.employee_data = None
        
        # 设置窗口属性
        self.setWindowTitle("员工详情")
        self.resize(900, 700)
        
        # 初始化UI
        self.initUI()
    
    def initUI(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # 标题
        self.title_label = QLabel("员工详情")
        self.title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        main_layout.addWidget(self.title_label)
        
        # 基本信息卡片
        basic_info_card = CardWidget(self)
        basic_info_layout = QFormLayout(basic_info_card)
        basic_info_layout.setLabelAlignment(Qt.AlignRight)
        basic_info_layout.setSpacing(15)
        basic_info_layout.setContentsMargins(20, 20, 20, 20)
        
        # 员工工号
        self.employee_no_edit = LineEdit(self)
        self.employee_no_edit.setPlaceholderText("员工工号")
        basic_info_layout.addRow("工号:", self.employee_no_edit)
        
        # 员工GID
        self.gid_edit = LineEdit(self)
        self.gid_edit.setPlaceholderText("员工GID")
        basic_info_layout.addRow("GID:", self.gid_edit)
        
        # 员工姓名
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("员工姓名")
        basic_info_layout.addRow("姓名:", self.name_edit)
        
        # 在职状态
        self.status_combo = ComboBox(self)
        self.status_combo.addItems(["在职", "离职", "休假", "其他"])
        basic_info_layout.addRow("状态:", self.status_combo)
        
        # 部门
        self.department_edit = LineEdit(self)
        self.department_edit.setPlaceholderText("员工所在部门")
        basic_info_layout.addRow("部门:", self.department_edit)
        
        main_layout.addWidget(basic_info_card)
        
        # 职级信息卡片
        grade_card = CardWidget(self)
        grade_layout = QVBoxLayout(grade_card)
        grade_layout.setContentsMargins(20, 20, 20, 20)
        
        grade_label = QLabel("职级信息")
        grade_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        grade_layout.addWidget(grade_label)
        
        grade_form = QFormLayout()
        grade_form.setLabelAlignment(Qt.AlignRight)
        grade_form.setSpacing(15)
        
        # 2020年职级
        self.grade_2020_combo = ComboBox(self)
        self.grade_2020_combo.addItems(["", "G1", "G2", "G3", "G4A", "G4B", "Technian"])
        grade_form.addRow("2020年职级:", self.grade_2020_combo)
        
        # 2021年职级
        self.grade_2021_combo = ComboBox(self)
        self.grade_2021_combo.addItems(["", "G1", "G2", "G3", "G4A", "G4B", "Technian"])
        grade_form.addRow("2021年职级:", self.grade_2021_combo)
        
        # 2022年职级
        self.grade_2022_combo = ComboBox(self)
        self.grade_2022_combo.addItems(["", "G1", "G2", "G3", "G4A", "G4B", "Technian"])
        grade_form.addRow("2022年职级:", self.grade_2022_combo)
        
        # 2023年职级
        self.grade_2023_combo = ComboBox(self)
        self.grade_2023_combo.addItems(["", "G1", "G2", "G3", "G4A", "G4B", "Technian"])
        grade_form.addRow("2023年职级:", self.grade_2023_combo)
        
        # 2024年职级
        self.grade_2024_combo = ComboBox(self)
        self.grade_2024_combo.addItems(["", "G1", "G2", "G3", "G4A", "G4B", "Technian"])
        grade_form.addRow("2024年职级:", self.grade_2024_combo)
        
        # 2025年职级
        self.grade_2025_combo = ComboBox(self)
        self.grade_2025_combo.addItems(["", "G1", "G2", "G3", "G4A", "G4B", "Technian"])
        grade_form.addRow("2025年职级:", self.grade_2025_combo)
        
        grade_layout.addLayout(grade_form)
        main_layout.addWidget(grade_card)
        
        # 备注信息
        notes_card = CardWidget(self)
        notes_layout = QVBoxLayout(notes_card)
        notes_layout.setContentsMargins(20, 20, 20, 20)
        
        notes_label = QLabel("备注信息")
        notes_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        notes_layout.addWidget(notes_label)
        
        self.notes_edit = TextEdit(self)
        self.notes_edit.setPlaceholderText("输入备注信息...")
        notes_layout.addWidget(self.notes_edit)
        
        main_layout.addWidget(notes_card)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_btn = PrimaryPushButton("保存", self)
        self.save_btn.setIcon(FluentIcon.SAVE)
        self.save_btn.clicked.connect(self.saveEmployee)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.setIcon(FluentIcon.CANCEL)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def loadEmployee(self, employee_id):
        """加载员工信息"""
        # 避免重复处理
        if self.isVisible():
            return
            
        self.employee_id = employee_id
        self.employee_data = self.db.get_employee_by_id(employee_id)
        
        if self.employee_data:
            # 更新标题
            self.title_label.setText(f"员工详情 - {self.employee_data.get('name', '')}")
            
            # 填充基本信息
            self.employee_no_edit.setText(str(self.employee_data.get('employee_no', '')))
            self.gid_edit.setText(str(self.employee_data.get('gid', '')))
            self.name_edit.setText(str(self.employee_data.get('name', '')))
            
            # 设置状态
            status = self.employee_data.get('status', '')
            index = self.status_combo.findText(status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
            
            self.department_edit.setText(str(self.employee_data.get('department', '')))
            
            # 设置职级信息
            self.setGradeComboValue(self.grade_2020_combo, self.employee_data.get('grade_2020', ''))
            self.setGradeComboValue(self.grade_2021_combo, self.employee_data.get('grade_2021', ''))
            self.setGradeComboValue(self.grade_2022_combo, self.employee_data.get('grade_2022', ''))
            self.setGradeComboValue(self.grade_2023_combo, self.employee_data.get('grade_2023', ''))
            self.setGradeComboValue(self.grade_2024_combo, self.employee_data.get('grade_2024', ''))
            self.setGradeComboValue(self.grade_2025_combo, self.employee_data.get('grade_2025', ''))
            
            # 设置备注
            self.notes_edit.setText(str(self.employee_data.get('notes', '')))
            
            # 显示对话框
            self.open()
    
    def setGradeComboValue(self, combo, value):
        """设置职级下拉框的值"""
        if value:
            index = combo.findText(value)
            if index >= 0:
                combo.setCurrentIndex(index)
            else:
                combo.setCurrentIndex(0)
        else:
            combo.setCurrentIndex(0)
    
    def saveEmployee(self):
        """保存员工信息"""
        if not self.employee_id:
            return
        
        # 收集更新后的数据
        updated_data = {
            'employee_no': self.employee_no_edit.text(),
            'gid': self.gid_edit.text(),
            'name': self.name_edit.text(),
            'status': self.status_combo.currentText(),
            'department': self.department_edit.text(),
            'grade_2020': self.grade_2020_combo.currentText(),
            'grade_2021': self.grade_2021_combo.currentText(),
            'grade_2022': self.grade_2022_combo.currentText(),
            'grade_2023': self.grade_2023_combo.currentText(),
            'grade_2024': self.grade_2024_combo.currentText(),
            'grade_2025': self.grade_2025_combo.currentText(),
            'notes': self.notes_edit.toPlainText()
        }
        
        # 检查必填字段
        if not updated_data['name'] or not updated_data['employee_no']:
            MessageBox(
                '保存失败',
                '员工姓名和工号为必填项，请检查输入',
                self
            ).exec()
            return
        
        # 执行更新
        success = self.db.update_employee(self.employee_id, updated_data, "管理员")
        
        if success:
            # 提示保存成功
            InfoBar.success(
                title='保存成功',
                content=f"员工 {updated_data['name']} 的信息已更新",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.parent
            )
            
            # 关闭对话框
            self.accept()
        else:
            # 提示保存失败
            MessageBox(
                '保存失败',
                '更新员工信息时发生错误，请稍后重试',
                self
            ).exec() 
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QTextEdit, QDialog, QDialogButtonBox,
    QComboBox, QGroupBox, QApplication, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSpinBox
)
from qfluentwidgets import (
    LineEdit, ComboBox, TextEdit, PrimaryPushButton, 
    PushButton, CardWidget, FluentIcon, InfoBar,
    InfoBarPosition, setTheme, Theme, MessageBox, IconWidget,
    EditableComboBox, SubtitleLabel, BodyLabel, SpinBox,
    TableWidget, TitleLabel
)
import datetime

class EmployeeDetailView(QDialog):
    """员工详情视图，用于查看和编辑员工信息"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent = parent
        self.employee_id = None
        self.employee_data = None
        self.grades = []  # 存储职级历史记录
        
        # 设置窗口属性
        self.setWindowTitle("员工详情")
        self.resize(900, 700)
        
        # 初始化UI
        self.initUI()
    
    def initUI(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题卡片
        title_layout = QHBoxLayout()
        
        # 使用标题标签
        self.title_label = TitleLabel("员工详情")
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch(1)
        
        main_layout.addLayout(title_layout)
        
        # 基本信息卡片 - 使用更紧凑的布局
        basic_info_card = CardWidget(self)
        basic_info_layout = QVBoxLayout(basic_info_card)
        basic_info_layout.setContentsMargins(20, 15, 20, 15)
        basic_info_layout.setSpacing(10)
        
        # 使用两列布局使基本信息更紧凑
        top_row_layout = QHBoxLayout()
        top_row_layout.setSpacing(20)
        
        # 左侧列
        left_form = QFormLayout()
        left_form.setLabelAlignment(Qt.AlignRight)
        left_form.setSpacing(10)
        
        # 员工工号
        self.employee_no_edit = LineEdit(self)
        self.employee_no_edit.setPlaceholderText("员工工号")
        left_form.addRow("工号:", self.employee_no_edit)
        
        # 员工GID
        self.gid_edit = LineEdit(self)
        self.gid_edit.setPlaceholderText("员工GID")
        left_form.addRow("GID:", self.gid_edit)
        
        top_row_layout.addLayout(left_form)
        
        # 右侧列
        right_form = QFormLayout()
        right_form.setLabelAlignment(Qt.AlignRight)
        right_form.setSpacing(10)
        
        # 员工姓名
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("员工姓名")
        right_form.addRow("姓名:", self.name_edit)
        
        # 部门 - 使用EditableComboBox代替LineEdit
        self.department_edit = EditableComboBox(self)
        self.department_edit.setPlaceholderText("请选择或输入部门")
        right_form.addRow("部门:", self.department_edit)
        
        top_row_layout.addLayout(right_form)
        
        basic_info_layout.addLayout(top_row_layout)
        
        # 状态行
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        status_label = QLabel("状态:", self)
        status_label.setFixedWidth(40)
        status_layout.addWidget(status_label)
        
        # 在职状态下拉框
        self.status_combo = ComboBox(self)
        self.status_combo.addItems(["正常工作", "长期歇假", "自定义..."])
        status_layout.addWidget(self.status_combo)
        
        # 自定义状态输入框
        self.custom_status_edit = LineEdit(self)
        self.custom_status_edit.setPlaceholderText("请输入自定义状态")
        self.custom_status_edit.setVisible(False)  # 默认隐藏
        status_layout.addWidget(self.custom_status_edit)
        
        # 当选择"自定义..."时显示自定义状态输入框
        def on_status_changed(text):
            if text == "自定义...":
                self.custom_status_edit.setVisible(True)
                self.custom_status_edit.setFocus()
            else:
                self.custom_status_edit.setVisible(False)
        
        self.status_combo.currentTextChanged.connect(on_status_changed)
        
        basic_info_layout.addLayout(status_layout)
        
        main_layout.addWidget(basic_info_card)
        
        # 职级历史卡片 - 增加高度和改进表格布局
        grade_card = CardWidget(self)
        grade_layout = QVBoxLayout(grade_card)
        grade_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题和添加按钮所在的水平布局
        grade_title_layout = QHBoxLayout()
        
        grade_label = TitleLabel("职级历史")
        grade_title_layout.addWidget(grade_label)
        
        grade_title_layout.addStretch(1)
        
        # 添加职级按钮
        self.add_grade_btn = PushButton("添加职级", self)
        self.add_grade_btn.setIcon(FluentIcon.ADD)
        self.add_grade_btn.clicked.connect(self.addGrade)
        grade_title_layout.addWidget(self.add_grade_btn)
        
        grade_layout.addLayout(grade_title_layout)
        
        # 职级历史表格 - 改进表格显示
        self.grade_table = TableWidget(self)
        self.grade_table.setColumnCount(4)
        self.grade_table.setHorizontalHeaderLabels(["年份", "职级", "备注", "操作"])
        self.grade_table.setMinimumHeight(150)  # 设置最小高度，确保表格有足够空间
        
        # 自定义列宽度，不再使用Stretch模式
        self.grade_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.grade_table.setColumnWidth(0, 100)  # 年份列
        self.grade_table.setColumnWidth(1, 100)  # 职级列
        self.grade_table.setColumnWidth(2, 350)  # 备注列
        self.grade_table.setColumnWidth(3, 150)  # 操作列 - 确保有足够宽度显示按钮
        
        self.grade_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.grade_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.grade_table.verticalHeader().setVisible(False)  # 隐藏行号
        
        grade_layout.addWidget(self.grade_table)
        
        main_layout.addWidget(grade_card)
        
        # 备注信息
        notes_card = CardWidget(self)
        notes_layout = QVBoxLayout(notes_card)
        notes_layout.setContentsMargins(20, 15, 20, 15)  # 减小内边距
        
        notes_label = TitleLabel("备注信息")
        notes_layout.addWidget(notes_label)
        
        self.notes_edit = TextEdit(self)
        self.notes_edit.setPlaceholderText("输入备注信息...")
        self.notes_edit.setMaximumHeight(120)  # 限制最大高度
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
    
    def loadEmployee(self, employee_no):
        """加载员工信息"""
        # 保存当前工号
        self.employee_id = employee_no  # 保持变量名，但存储的是employee_no
        self.employee_data = self.db.get_employee_by_no(employee_no)
        
        if not self.employee_data:
            print(f"找不到工号为 {employee_no} 的员工")
            return
            
        # 更新标题
        self.title_label.setText(f"员工详情 - {self.employee_data.get('name', '')}")
        
        # 填充基本信息
        self.employee_no_edit.setText(str(self.employee_data.get('employee_no', '')))
        self.gid_edit.setText(str(self.employee_data.get('gid', '')))
        self.name_edit.setText(str(self.employee_data.get('name', '')))
        
        # 设置状态
        status = self.employee_data.get('status', '')
        if status in ["正常工作", "长期歇假"]:
            self.status_combo.setCurrentText(status)
        else:
            # 对于自定义状态，设置为"自定义..."并填充自定义状态输入框
            self.status_combo.setCurrentText("自定义...")
            self.custom_status_edit.setText(status)
        
        # 获取所有部门列表
        departments = set()
        employees = self.db.get_all_employees()
        for emp in employees:
            if emp.get('department'):
                departments.add(emp.get('department'))
                
        # 添加部门到下拉框
        self.department_edit.clear()
        for dept in sorted(departments):
            self.department_edit.addItem(dept)
            
        # 设置当前部门
        current_dept = str(self.employee_data.get('department', ''))
        if current_dept:
            # 如果当前部门在列表中，设置为当前选中项
            if current_dept in departments:
                self.department_edit.setCurrentText(current_dept)
            else:
                # 如果不在列表中，添加并设置为当前选中项
                self.department_edit.addItem(current_dept)
                self.department_edit.setCurrentText(current_dept)
        
        # 加载职级历史
        self.loadGradeHistory()
        
        # 设置备注
        self.notes_edit.setText(str(self.employee_data.get('notes', '')))
        
        # 如果窗口还没显示，则显示窗口
        if not self.isVisible():
            # 在第一次显示时确保窗口居中
            screen = QApplication.desktop().screenGeometry()
            size = self.geometry()
            x = (screen.width() - size.width()) // 2
            y = (screen.height() - size.height()) // 2
            self.move(x, y)
            self.show()
    
    def loadGradeHistory(self):
        """加载员工职级历史"""
        # 清空表格
        self.grade_table.setRowCount(0)
        
        # 获取职级历史 - 使用工号获取
        self.grades = self.db.get_employee_grades_by_no(self.employee_id)
        
        # 填充表格
        for row, grade in enumerate(self.grades):
            self.grade_table.insertRow(row)
            
            # 年份
            year_item = QTableWidgetItem(str(grade.get('year', '')))
            year_item.setTextAlignment(Qt.AlignCenter)
            self.grade_table.setItem(row, 0, year_item)
            
            # 职级
            grade_item = QTableWidgetItem(str(grade.get('grade', '')))
            grade_item.setTextAlignment(Qt.AlignCenter)
            self.grade_table.setItem(row, 1, grade_item)
            
            # 备注
            comment_item = QTableWidgetItem(str(grade.get('comment', '')))
            comment_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.grade_table.setItem(row, 2, comment_item)
            
            # 操作按钮 - 编辑和删除
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)
            action_layout.setSpacing(10)
            action_layout.setAlignment(Qt.AlignCenter)
            
            # 使用PushButton并设置为图标按钮格式
            edit_btn = PushButton(parent=action_widget)
            edit_btn.setIcon(FluentIcon.EDIT)
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip("编辑")
            edit_btn.setStyleSheet("PushButton { border: none; background-color: transparent; padding: 0; margin: 0; }")
            
            delete_btn = PushButton(parent=action_widget)
            delete_btn.setIcon(FluentIcon.DELETE)
            delete_btn.setFixedSize(28, 28)
            delete_btn.setToolTip("删除")
            delete_btn.setStyleSheet("PushButton { border: none; background-color: transparent; padding: 0; margin: 0; }")
            
            # 使用闭包捕获当前行的grade_id
            grade_id = grade.get('id')
            
            # 连接信号和槽
            edit_btn.clicked.connect(lambda checked, gid=grade_id: self.editGrade(gid))
            delete_btn.clicked.connect(lambda checked, gid=grade_id: self.deleteGrade(gid))
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            
            self.grade_table.setCellWidget(row, 3, action_widget)
            
        # 确保表格有足够高度显示所有行
        if len(self.grades) > 0:
            # 计算表格需要的最小高度：表头高度 + 每行高度 * 行数（最多6行，超过滚动显示）
            header_height = self.grade_table.horizontalHeader().height()
            row_height = self.grade_table.rowHeight(0)
            visible_rows = min(len(self.grades), 6)  # 最多显示6行，超过则滚动
            min_height = header_height + row_height * visible_rows + 10  # 添加一些额外空间
            
            self.grade_table.setMinimumHeight(min_height)
        
        # 如果没有记录，显示提示文本
        if len(self.grades) == 0:
            self.grade_table.setRowCount(1)
            empty_item = QTableWidgetItem("暂无职级记录，点击\"添加职级\"按钮添加")
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.grade_table.setSpan(0, 0, 1, 4)  # 合并单元格
            self.grade_table.setItem(0, 0, empty_item)
            
            # 设置最小高度，确保空表格也有适当的显示空间
            self.grade_table.setMinimumHeight(80)
    
    def addGrade(self):
        """添加新的职级记录"""
        if not self.employee_id:
            return
            
        # 创建对话框
        dialog = GradeDialog(self)
        dialog.setWindowTitle("添加职级记录")
        
        # 显示对话框
        if dialog.exec_():
            year = dialog.year_spin.value()
            grade = dialog.grade_combo.currentText()
            comment = dialog.comment_edit.toPlainText()
            
            # 保存到数据库
            success = self.db.add_employee_grade_by_no(
                employee_no=self.employee_id,
                year=year,
                grade=grade,
                comment=comment,
                user="管理员"
            )
            
            if success:
                # 重新加载职级历史
                self.loadGradeHistory()
                
                # 显示成功消息
                InfoBar.success(
                    title='添加成功',
                    content=f"已成功添加{year}年职级记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def editGrade(self, grade_id):
        """编辑职级记录"""
        # 查找对应的职级记录
        grade = next((g for g in self.grades if g.get('id') == grade_id), None)
        
        if not grade:
            return
            
        # 创建对话框
        dialog = GradeDialog(self)
        dialog.setWindowTitle("编辑职级记录")
        
        # 填充现有数据
        dialog.year_spin.setValue(int(grade.get('year', datetime.datetime.now().year)))
        dialog.grade_combo.setCurrentText(str(grade.get('grade', '')))
        dialog.comment_edit.setText(str(grade.get('comment', '')))
        
        # 显示对话框
        if dialog.exec_():
            year = dialog.year_spin.value()
            grade_value = dialog.grade_combo.currentText()
            comment = dialog.comment_edit.toPlainText()
            
            # 更新数据库
            success = self.db.add_employee_grade_by_no(
                employee_no=self.employee_id,
                year=year,
                grade=grade_value,
                comment=comment,
                user="管理员"
            )
            
            if success:
                # 重新加载职级历史
                self.loadGradeHistory()
                
                # 显示成功消息
                InfoBar.success(
                    title='更新成功',
                    content=f"已成功更新{year}年职级记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def deleteGrade(self, grade_id):
        """删除职级记录"""
        # 查找对应的职级记录
        grade = next((g for g in self.grades if g.get('id') == grade_id), None)
        
        if not grade:
            return
            
        # 确认删除
        reply = MessageBox(
            '确认删除',
            f"确定要删除{grade.get('year')}年的职级记录吗？",
            self
        )
        
        # 修复MessageBox处理
        yes_button = reply.yesButton
        reply.yesButton.setText('是')
        reply.cancelButton.setText('否')
        
        if reply.exec():
            # 执行删除
            success = self.db.delete_employee_grade(grade_id, "管理员")
            
            if success:
                # 重新加载职级历史
                self.loadGradeHistory()
                
                # 显示成功消息
                InfoBar.success(
                    title='删除成功',
                    content=f"已成功删除{grade.get('year')}年职级记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def saveEmployee(self):
        """保存员工信息"""
        if not self.employee_id:
            return
        
        # 获取状态
        if self.status_combo.currentText() == "自定义...":
            status_value = self.custom_status_edit.text()
            if not status_value.strip():
                # 如果自定义状态为空，显示错误提示
                MessageBox(
                    '保存失败',
                    '请输入自定义状态或选择预设状态',
                    self
                ).exec()
                return
        else:
            status_value = self.status_combo.currentText()
        
        # 收集更新后的数据
        notes_text = self.notes_edit.toPlainText() or ""  # 确保notes为空字符串而不是None
        
        updated_data = {
            'employee_no': self.employee_no_edit.text(),
            'gid': self.gid_edit.text(),
            'name': self.name_edit.text(),
            'status': status_value,
            'department': self.department_edit.currentText(),
            'notes': notes_text
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
        success = self.db.update_employee_by_no(self.employee_id, updated_data, "管理员")
        
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


class GradeDialog(QDialog):
    """职级编辑对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("职级记录")
        self.resize(450, 350)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 添加说明文本
        info_label = SubtitleLabel("请填写员工职级信息", self)
        layout.addWidget(info_label)
        
        # 年份选择器
        year_card = CardWidget(self)
        year_card.setObjectName("yearCard")
        year_card_layout = QFormLayout(year_card)
        year_card_layout.setContentsMargins(15, 15, 15, 15)
        year_card_layout.setSpacing(10)
        year_card_layout.setLabelAlignment(Qt.AlignRight)
        
        current_year = datetime.datetime.now().year
        
        self.year_spin = SpinBox(self)
        self.year_spin.setRange(2000, current_year + 10)  # 允许设置未来几年
        self.year_spin.setValue(current_year)
        self.year_spin.setFixedWidth(120)
        year_card_layout.addRow(BodyLabel("年份:"), self.year_spin)
        
        # 职级选择
        self.grade_combo = EditableComboBox(self)
        self.grade_combo.addItems(["G1", "G2", "G3", "G4A", "G4B", "Technian"])
        self.grade_combo.setFixedWidth(120)
        year_card_layout.addRow(BodyLabel("职级:"), self.grade_combo)
        
        layout.addWidget(year_card)
        
        # 备注卡片
        comment_card = CardWidget(self)
        comment_card.setObjectName("commentCard")
        comment_layout = QVBoxLayout(comment_card)
        comment_layout.setContentsMargins(15, 15, 15, 15)
        comment_layout.setSpacing(10)
        
        comment_label = BodyLabel("备注:", self)
        comment_layout.addWidget(comment_label)
        
        self.comment_edit = TextEdit(self)
        self.comment_edit.setPlaceholderText("添加备注信息...")
        self.comment_edit.setMinimumHeight(80)
        comment_layout.addWidget(self.comment_edit)
        
        layout.addWidget(comment_card)
        
        # 按钮区域
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 设置中文按钮文本
        button_box.button(QDialogButtonBox.Ok).setText("确定")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # 设置样式
        self.setStyleSheet("""
            #yearCard, #commentCard {
                border-radius: 6px;
                background-color: #f5f5f5;
            }
        """) 
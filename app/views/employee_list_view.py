from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QFont, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QHeaderView, QMessageBox, QLabel, QFrame,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QTextEdit, QComboBox, QSpinBox,
    QAbstractItemView
)
from qfluentwidgets import (
    SearchLineEdit, PushButton, InfoBar, InfoBarPosition,
    ComboBox, CardWidget, TableWidget, ToolButton, 
    FluentIcon as FIF, TransparentToolButton, SubtitleLabel,
    ToolTipFilter, ToolTipPosition, ScrollArea, Dialog, 
    MessageBoxBase, StateToolTip, LineEdit, TextEdit, MessageBox,
    BodyLabel, StrongBodyLabel, SpinBox, EditableComboBox
)
from ..utils.resource_loader import get_resource_path
import datetime

class EmployeeListView(QWidget):
    """员工列表视图 - Fluent Design风格"""
    
    # 自定义信号，当选择员工时发出
    employeeSelected = pyqtSignal(object)
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent = parent
        self.selected_employee_id = None
        
        # 初始化UI
        self.initUI()
        
        # 加载员工数据
        self.loadEmployeeData()
    
    def initUI(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题
        self.title_label = SubtitleLabel("员工管理", self)
        self.title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        main_layout.addWidget(self.title_label)
        
        # 顶部工具栏
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
        # 搜索框
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("搜索员工（姓名、工号、GID或部门）")
        self.search_edit.setFixedWidth(320)
        self.search_edit.textChanged.connect(self.filterEmployees)
        top_bar.addWidget(self.search_edit)
        
        top_bar.addStretch(1)
        
        # 部门筛选下拉框
        dept_container = QWidget()
        dept_layout = QHBoxLayout(dept_container)
        dept_layout.setContentsMargins(0, 0, 0, 0)
        dept_layout.setSpacing(5)
        
        dept_label = QLabel("部门:", self)
        dept_layout.addWidget(dept_label)
        
        self.department_filter = ComboBox(self)
        self.department_filter.setPlaceholderText("全部")
        self.department_filter.setMinimumWidth(120)
        self.department_filter.currentTextChanged.connect(self.filterEmployees)
        dept_layout.addWidget(self.department_filter)
        
        top_bar.addWidget(dept_container)
        
        # 职级筛选下拉框
        grade_container = QWidget()
        grade_layout = QHBoxLayout(grade_container)
        grade_layout.setContentsMargins(0, 0, 0, 0)
        grade_layout.setSpacing(5)
        
        grade_label = QLabel("职级:", self)
        grade_layout.addWidget(grade_label)
        
        self.grade_filter = ComboBox(self)
        self.grade_filter.setPlaceholderText("全部")
        self.grade_filter.setMinimumWidth(100)
        self.grade_filter.addItems(["全部", "G1", "G2", "G3", "G4A", "G4B", "Technian"])
        self.grade_filter.currentTextChanged.connect(self.filterEmployees)
        grade_layout.addWidget(self.grade_filter)
        
        top_bar.addWidget(grade_container)
        
        # 操作按钮
        self.refresh_btn = TransparentToolButton(FIF.SYNC, self)
        self.refresh_btn.setToolTip("刷新")
        self.refresh_btn.clicked.connect(self.refreshEmployeeList)
        top_bar.addWidget(self.refresh_btn)
        
        self.add_btn = PushButton('添加员工', self)
        self.add_btn.setIcon(FIF.ADD)
        self.add_btn.clicked.connect(self.addEmployee)
        top_bar.addWidget(self.add_btn)
        
        main_layout.addLayout(top_bar)
        
        # 表格容器卡片
        self.table_card = CardWidget(self)
        card_layout = QVBoxLayout(self.table_card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        
        # 使用 TableWidget 替代 QTableView
        self.table_view = TableWidget(self.table_card)
        self.table_view.setBorderVisible(True)
        self.table_view.setBorderRadius(8)
        self.table_view.setWordWrap(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setColumnCount(7)
        self.table_view.verticalHeader().hide()
        self.table_view.setHorizontalHeaderLabels(['工号', 'GID', '姓名', '部门', '当前职级', '状态', '备注'])
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSortingEnabled(True)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁用直接编辑
        
        # 连接表格项点击信号
        self.table_view.cellClicked.connect(self.onTableClicked)
        self.table_view.cellDoubleClicked.connect(self.onTableDoubleClicked)
        
        card_layout.addWidget(self.table_view)
        
        main_layout.addWidget(self.table_card)
        
        # 底部工具栏
        bottom_bar = QHBoxLayout()
        
        # 操作按钮组
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        self.edit_btn = PushButton('编辑', button_container)
        self.edit_btn.setIcon(FIF.EDIT)
        self.edit_btn.clicked.connect(self.editEmployee)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = PushButton('删除', button_container)
        self.delete_btn.setIcon(FIF.DELETE)
        self.delete_btn.clicked.connect(self.deleteEmployee)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        bottom_bar.addWidget(button_container)
        
        bottom_bar.addStretch(1)
        
        # 状态信息
        self.status_container = QWidget()
        status_layout = QHBoxLayout(self.status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)
        
        # 创建状态图标和文本
        info_icon = TransparentToolButton(FIF.INFO, self.status_container)
        info_icon.setFixedSize(20, 20)
        info_icon.setIconSize(QSize(16, 16))
        status_layout.addWidget(info_icon)
        
        self.count_label = QLabel('总计: 0 名员工', self.status_container)
        status_layout.addWidget(self.count_label)
        
        bottom_bar.addWidget(self.status_container)
        
        main_layout.addLayout(bottom_bar)
        
        # 设置布局
        self.setLayout(main_layout)
    
    def loadEmployeeData(self, apply_filter=True):
        """加载员工数据"""
        # 保存当前筛选条件
        current_dept = self.department_filter.currentText()
        current_grade = self.grade_filter.currentText()
        search_text = self.search_edit.text()
        
        # 保存排序状态
        sort_column = self.table_view.horizontalHeader().sortIndicatorSection()
        sort_order = self.table_view.horizontalHeader().sortIndicatorOrder()
        
        # 临时禁用排序功能，避免在加载数据过程中触发排序
        self.table_view.setSortingEnabled(False)
        
        # 清除表格数据
        self.table_view.clearContents()
        self.table_view.setRowCount(0)
        
        # 获取员工数据
        employees = self.db.get_all_employees()
        
        # 加载部门列表到筛选下拉框
        departments = set()
        for emp in employees:
            if emp.get('department'):
                departments.add(emp.get('department'))
        
        # 更新部门下拉框
        self.department_filter.clear()
        self.department_filter.addItem("全部")
        for dept in sorted(departments):
            self.department_filter.addItem(dept)
        
        # 如果之前有选中的部门，则恢复选中
        if current_dept and current_dept in departments:
            self.department_filter.setCurrentText(current_dept)
        
        # 设置表格行数
        self.table_view.setRowCount(len(employees))
        
        # 添加员工数据到表格
        for row, emp in enumerate(employees):
            # 获取最新年份的职级
            latest_grade = self.getLatestGrade(emp)
            
            # 获取备注并处理长文本
            notes = emp.get('notes', '')
            if notes is None:  # 确保None值显示为空字符串
                notes = ""
            else:
                notes = str(notes)
            
            truncated_notes = notes
            if len(notes) > 30:  # 限制备注显示长度为30个字符
                truncated_notes = notes[:27] + "..."
            
            # 添加表格项，不再包含ID列
            self.table_view.setItem(row, 0, QTableWidgetItem(str(emp.get('employee_no', ''))))
            self.table_view.setItem(row, 1, QTableWidgetItem(str(emp.get('gid', ''))))
            self.table_view.setItem(row, 2, QTableWidgetItem(str(emp.get('name', ''))))
            self.table_view.setItem(row, 3, QTableWidgetItem(str(emp.get('department', ''))))
            self.table_view.setItem(row, 4, QTableWidgetItem(str(latest_grade)))
            self.table_view.setItem(row, 5, QTableWidgetItem(str(emp.get('status', ''))))
            self.table_view.setItem(row, 6, QTableWidgetItem(truncated_notes))
            
            # 在工号列中存储employee_no作为用户数据，用于标识
            self.table_view.item(row, 0).setData(Qt.UserRole, emp.get('employee_no'))
            
            # 如果备注被截断，添加工具提示显示完整内容
            if len(notes) > 30:
                self.table_view.item(row, 6).setToolTip(notes)
                
        # 设置表格列宽
        self.table_view.setColumnWidth(0, 80)  # ID
        self.table_view.setColumnWidth(1, 120)  # 工号
        self.table_view.setColumnWidth(2, 120)  # GID
        self.table_view.setColumnWidth(3, 150)  # 姓名
        self.table_view.setColumnWidth(4, 150)  # 部门
        self.table_view.setColumnWidth(5, 100)  # 职级
        self.table_view.setColumnWidth(6, 100)  # 状态
        
        # 更新员工计数
        self.count_label.setText(f'总计: {len(employees)} 名员工')
        
        # 重新启用排序功能
        self.table_view.setSortingEnabled(True)
        
        # 恢复之前的排序状态
        self.table_view.horizontalHeader().setSortIndicator(sort_column, sort_order)
        
        # 应用过滤器
        if apply_filter and (search_text or current_dept != "全部" or current_grade != "全部"):
            self.filterEmployees()
    
    def getLatestGrade(self, employee):
        """获取员工最新的职级"""
        # 从旧的字段中查找职级（使用最新年份）
        grades = {}
        
        # 查找所有带年份的职级字段
        for key, value in employee.items():
            if key.startswith('grade_') and value:
                try:
                    # 提取年份
                    year = int(key.split('_')[1])
                    grades[year] = value
                except (ValueError, IndexError):
                    continue
        
        # 如果没有找到任何职级，返回空字符串
        if not grades:
            return ""
        
        # 返回最大年份的职级
        latest_year = max(grades.keys())
        return f"{grades[latest_year]} ({latest_year})"
    
    def refreshEmployeeList(self):
        """刷新员工列表"""
        try:
            # 显示刷新状态提示
            state_tooltip = StateToolTip("正在刷新", "正在加载员工数据...", self.parent)
            state_tooltip.move(self.parent.width() // 2 - state_tooltip.width() // 2,
                            self.parent.height() // 2 - state_tooltip.height() // 2)
            state_tooltip.show()
            
            # 记录加载前的行数，用于检测刷新后是否有数据
            before_rows = self.table_view.rowCount()
            
            # 加载数据
            self.loadEmployeeData()
            
            # 检查加载后的行数，确保数据正常加载
            after_rows = self.table_view.rowCount()
            if after_rows == 0 and before_rows > 0:
                print("警告：刷新后表格为空，可能存在数据加载问题")
            
            # 更新状态提示并自动关闭
            state_tooltip.setContent("数据刷新完成")
            state_tooltip.setState(True)
            
            # 显示成功信息
            InfoBar.success(
                title='刷新成功',
                content=f'员工数据已更新，共 {after_rows} 名员工',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"刷新员工列表失败: {e}\n{error_details}")
            
            # 如果有状态提示，关闭它
            try:
                if 'state_tooltip' in locals() and state_tooltip:
                    state_tooltip.setContent("刷新失败")
                    state_tooltip.setState(False)
            except:
                pass
                
            # 显示错误消息
            InfoBar.error(
                title='刷新失败',
                content=f"刷新员工列表时发生错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def filterEmployees(self):
        """根据搜索条件过滤员工列表"""
        try:
            search_text = self.search_edit.text().lower()
            department = self.department_filter.currentText()
            grade = self.grade_filter.currentText()
            
            # 保存排序状态
            sort_column = self.table_view.horizontalHeader().sortIndicatorSection()
            sort_order = self.table_view.horizontalHeader().sortIndicatorOrder()
            
            # 遍历所有行，根据条件显示或隐藏
            for row in range(self.table_view.rowCount()):
                # 安全获取单元格文本
                def get_cell_text(row, col):
                    item = self.table_view.item(row, col)
                    if not item:
                        return ""
                    if col == 0:  # ID列特殊处理
                        return str(item.data(Qt.DisplayRole)).lower()
                    return item.text().lower()
                
                # 跳过空行或无效行
                if self.table_view.item(row, 0) is None:
                    continue
                
                employee_no = get_cell_text(row, 0)
                gid = get_cell_text(row, 1)
                name = get_cell_text(row, 2)
                dept = get_cell_text(row, 3)
                emp_grade = get_cell_text(row, 4)
                status = get_cell_text(row, 5)
                notes = get_cell_text(row, 6)
                
                # 检查是否符合搜索文本条件
                text_match = search_text == "" or \
                            search_text in employee_no or \
                            search_text in gid or \
                            search_text in name or \
                            search_text in dept or \
                            search_text in emp_grade or \
                            search_text in status or \
                            search_text in notes
                
                # 检查是否符合部门筛选条件
                dept_match = department == "全部" or department.lower() == dept
                
                # 检查是否符合职级筛选条件
                grade_match = grade == "全部" or (grade.lower() in emp_grade.lower())
                
                # 如果符合所有条件，则显示该行，否则隐藏
                self.table_view.setRowHidden(row, not (text_match and dept_match and grade_match))
            
            # 确保排序状态保持不变
            self.table_view.horizontalHeader().setSortIndicator(sort_column, sort_order)
            
            # 更新显示的员工计数
            visible_count = sum(1 for row in range(self.table_view.rowCount()) if not self.table_view.isRowHidden(row))
            self.count_label.setText(f'总计: {visible_count} 名员工')
        except Exception as e:
            print(f"筛选员工列表失败: {e}")
            InfoBar.error(
                title='筛选失败',
                content=f"筛选员工列表时发生错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def onTableClicked(self, row, column):
        """表格项被单击时的处理函数"""
        try:
            # 检查该行是否有效
            if row < 0 or row >= self.table_view.rowCount():
                return
                
            # 安全获取数据
            employee_item = self.table_view.item(row, 0)  # 工号列
            if employee_item is None:
                return
                
            # 获取员工编号
            employee_no = employee_item.data(Qt.UserRole) or employee_item.text()
            if not employee_no:
                return
                
            self.selected_employee_id = employee_no
            
            # 启用编辑和删除按钮
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        except Exception as e:
            print(f"选择员工失败: {e}")
            self.selected_employee_id = None
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def onTableDoubleClicked(self, row, column):
        """表格项被双击时的处理函数"""
        try:
            # 检查该行是否有效
            if row < 0 or row >= self.table_view.rowCount():
                return
                
            # 安全获取数据
            employee_item = self.table_view.item(row, 0)  # 工号列
            if employee_item is None:
                return
                
            # 获取员工编号
            employee_no = employee_item.data(Qt.UserRole) or employee_item.text()
            if not employee_no:
                return
                
            # 发送信号，显示员工详情
            self.employeeSelected.emit(employee_no)
        except Exception as e:
            print(f"打开员工详情失败: {e}")
            InfoBar.error(
                title='操作失败',
                content="无法打开员工详情",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def addEmployee(self):
        """添加员工功能"""
        try:
            # 创建自定义对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout
            
            class EmployeeDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("添加员工")
                    self.resize(500, 550)
                    
                    # 创建表单布局
                    self.main_layout = QVBoxLayout(self)
                    self.form_layout = QFormLayout()
                    
                    # 创建输入字段
                    self.emp_no_edit = LineEdit(self)
                    self.emp_no_edit.setPlaceholderText("请输入工号")
                    
                    self.gid_edit = LineEdit(self)
                    self.gid_edit.setPlaceholderText("请输入GID")
                    
                    self.name_edit = LineEdit(self)
                    self.name_edit.setPlaceholderText("请输入姓名")
                    
                    # 部门下拉框
                    self.department_edit = EditableComboBox(self)
                    self.department_edit.setPlaceholderText("请选择或输入部门")
                    
                    # 初始职级下拉框
                    grade_container = QWidget()
                    grade_layout = QHBoxLayout(grade_container)
                    grade_layout.setContentsMargins(0, 0, 0, 0)
                    grade_layout.setSpacing(5)
                    
                    self.grade_edit = ComboBox(grade_container)
                    self.grade_edit.addItems(["G1", "G2", "G3", "G4A", "G4B", "Technian"])
                    self.grade_edit.setCurrentText("G1")
                    grade_layout.addWidget(self.grade_edit)
                    
                    # 年份选择器
                    current_year = datetime.datetime.now().year
                    
                    self.year_spin = SpinBox(grade_container)
                    self.year_spin.setRange(2000, current_year + 10)
                    self.year_spin.setValue(current_year)
                    grade_layout.addWidget(self.year_spin)
                    
                    # 状态选择框及自定义状态输入框
                    self.status_container = QWidget(self)
                    self.status_layout = QHBoxLayout(self.status_container)
                    self.status_layout.setContentsMargins(0, 0, 0, 0)
                    self.status_layout.setSpacing(10)
                    
                    self.status_edit = ComboBox(self.status_container)
                    self.status_edit.addItems(["正常工作", "长期歇假", "自定义..."])
                    self.status_edit.setCurrentText("正常工作")
                    self.status_layout.addWidget(self.status_edit)
                    
                    self.custom_status_edit = LineEdit(self.status_container)
                    self.custom_status_edit.setPlaceholderText("请输入自定义状态")
                    self.custom_status_edit.setVisible(False)  # 默认隐藏
                    self.status_layout.addWidget(self.custom_status_edit)
                    
                    # 当选择"自定义..."时显示自定义状态输入框
                    self.status_edit.currentTextChanged.connect(self.on_status_changed)
                    
                    # 备注输入框
                    self.notes_edit = TextEdit(self)
                    self.notes_edit.setPlaceholderText("备注信息")
                    self.notes_edit.setMaximumHeight(100)
                    
                    # 添加到表单布局
                    self.form_layout.addRow(BodyLabel("工号:"), self.emp_no_edit)
                    self.form_layout.addRow(BodyLabel("GID:"), self.gid_edit)
                    self.form_layout.addRow(BodyLabel("姓名:"), self.name_edit)
                    self.form_layout.addRow(BodyLabel("部门:"), self.department_edit)
                    self.form_layout.addRow(BodyLabel("当前职级:"), grade_container)
                    self.form_layout.addRow(BodyLabel("状态:"), self.status_container)
                    self.form_layout.addRow(BodyLabel("备注:"), self.notes_edit)
                    
                    self.main_layout.addLayout(self.form_layout)
                    
                    # 创建按钮
                    self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
                    self.button_box.accepted.connect(self.accept)
                    self.button_box.rejected.connect(self.reject)
                    self.main_layout.addWidget(self.button_box)
                
                def on_status_changed(self, text):
                    """状态选择改变时的处理函数"""
                    if text == "自定义...":
                        self.custom_status_edit.setVisible(True)
                        self.custom_status_edit.setFocus()
                    else:
                        self.custom_status_edit.setVisible(False)
                
                def get_employee_data(self):
                    """获取员工数据"""
                    # 获取状态
                    if self.status_edit.currentText() == "自定义...":
                        status_value = self.custom_status_edit.text()
                    else:
                        status_value = self.status_edit.currentText()
                    
                    return {
                        'employee_no': self.emp_no_edit.text(),
                        'gid': self.gid_edit.text(),
                        'name': self.name_edit.text(),
                        'department': self.department_edit.currentText(),
                        'status': status_value,
                        'notes': self.notes_edit.toPlainText(),
                        # 添加职级信息
                        'initial_grade': {
                            'year': self.year_spin.value(),
                            'grade': self.grade_edit.currentText()
                        }
                    }
            
            # 创建并显示对话框
            dialog = EmployeeDialog(self)
            
            # 获取现有部门列表
            departments = set()
            for row in range(self.table_view.rowCount()):
                dept = self.table_view.item(row, 3)
                if dept and dept.text():
                    departments.add(dept.text())
            
            # 添加部门到下拉框
            dialog.department_edit.addItems(sorted(list(departments)))
            
            # 显示对话框
            if dialog.exec_():
                # 获取员工数据
                employee_data = dialog.get_employee_data()
                
                # 添加员工到数据库
                success = self.db.add_employee(employee_data, "管理员")
                
                if success:
                    # 添加初始职级记录
                    initial_grade = employee_data.get('initial_grade')
                    if initial_grade:
                        # 获取新添加的员工ID
                        self.db.cursor.execute("SELECT last_insert_rowid()")
                        employee_id = self.db.cursor.fetchone()[0]
                        
                        # 添加职级记录
                        self.db.add_employee_grade(
                            employee_id=employee_id,
                            year=initial_grade['year'],
                            grade=initial_grade['grade'],
                            comment="初始职级",
                            user="管理员"
                        )
                    
                    # 刷新列表
                    self.refreshEmployeeList()
                    
                    # 显示成功消息
                    InfoBar.success(
                        title='添加成功',
                        content=f"已成功添加员工: {employee_data['name']}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title='添加失败',
                        content="添加员工时发生错误",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
        except Exception as e:
            InfoBar.error(
                title='添加失败',
                content=f"错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def editEmployee(self):
        """编辑员工功能"""
        if self.selected_employee_id is None:
            InfoBar.warning(
                title='未选择员工',
                content='请先选择要编辑的员工',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 发送信号，显示员工详情
        self.employeeSelected.emit(self.selected_employee_id)
    
    def deleteEmployee(self):
        """删除员工功能"""
        if self.selected_employee_id is None:
            InfoBar.warning(
                title='未选择员工',
                content='请先选择要删除的员工',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 确认删除对话框
        dialog = MessageBox(
            '确认删除',
            f'确定要删除工号为 {self.selected_employee_id} 的员工记录吗？此操作不可撤销。',
            self
        )
        
        # 设置按钮
        dialog.yesButton.setText('是')
        dialog.cancelButton.setText('否')
        
        # 显示对话框
        if dialog.exec_():
            try:
                # 执行删除操作
                success = self.db.delete_employee_by_no(self.selected_employee_id, "管理员")
                
                if success:
                    # 刷新列表
                    self.refreshEmployeeList()
                    
                    # 重置选中状态
                    self.selected_employee_id = None
                    self.edit_btn.setEnabled(False)
                    self.delete_btn.setEnabled(False)
                    
                    # 显示成功消息
                    InfoBar.success(
                        title='删除成功',
                        content='员工记录已成功删除',
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                else:
                    # 显示错误消息
                    InfoBar.error(
                        title='删除失败',
                        content='删除操作未能完成',
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
            except Exception as e:
                # 显示错误消息
                InfoBar.error(
                    title='删除失败',
                    content=f'错误: {str(e)}',
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                ) 
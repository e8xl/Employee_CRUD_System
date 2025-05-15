from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
    QHeaderView, QPushButton, QMessageBox, QLabel
)
from qfluentwidgets import (
    SearchLineEdit, PushButton, InfoBar, InfoBarPosition,
    ComboBox, CardWidget
)

class EmployeeListView(QWidget):
    """员工列表视图"""
    
    # 自定义信号，当选择员工时发出
    employeeSelected = pyqtSignal(int)
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent = parent
        
        # 初始化UI
        self.initUI()
        
        # 加载员工数据
        self.loadEmployeeData()
    
    def initUI(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部工具栏
        top_bar = QHBoxLayout()
        
        # 搜索框
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("搜索员工（姓名、工号、GID或部门）")
        self.search_edit.textChanged.connect(self.filterEmployees)
        top_bar.addWidget(self.search_edit)
        
        # 部门筛选下拉框
        self.department_filter = ComboBox(self)
        self.department_filter.setPlaceholderText("按部门筛选")
        self.department_filter.setMinimumWidth(150)
        self.department_filter.currentTextChanged.connect(self.filterEmployees)
        top_bar.addWidget(self.department_filter)
        
        # 职级筛选下拉框
        self.grade_filter = ComboBox(self)
        self.grade_filter.setPlaceholderText("按职级筛选")
        self.grade_filter.setMinimumWidth(150)
        self.grade_filter.addItems(["全部", "G1", "G2", "G3", "G4A", "G4B", "Technian"])
        self.grade_filter.currentTextChanged.connect(self.filterEmployees)
        top_bar.addWidget(self.grade_filter)
        
        # 操作按钮
        self.add_btn = PushButton('添加员工', self)
        self.add_btn.clicked.connect(self.addEmployee)
        top_bar.addWidget(self.add_btn)
        
        self.refresh_btn = PushButton('刷新', self)
        self.refresh_btn.clicked.connect(self.refreshEmployeeList)
        top_bar.addWidget(self.refresh_btn)
        
        main_layout.addLayout(top_bar)
        
        # 表格视图
        self.table_card = CardWidget(self)
        table_layout = QVBoxLayout(self.table_card)
        
        self.table_view = QTableView(self)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.horizontalHeader().setHighlightSections(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.clicked.connect(self.onTableClicked)
        self.table_view.doubleClicked.connect(self.onTableDoubleClicked)
        
        # 设置模型
        self.model = QStandardItemModel(0, 8, self)
        self.model.setHorizontalHeaderLabels(['ID', '工号', 'GID', '姓名', '部门', '当前职级', '状态', '备注'])
        
        # 使用排序代理模型
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # 在所有列上进行过滤
        
        self.table_view.setModel(self.proxy_model)
        
        table_layout.addWidget(self.table_view)
        main_layout.addWidget(self.table_card)
        
        # 底部工具栏
        bottom_bar = QHBoxLayout()
        
        self.edit_btn = PushButton('编辑', self)
        self.edit_btn.clicked.connect(self.editEmployee)
        self.edit_btn.setEnabled(False)
        bottom_bar.addWidget(self.edit_btn)
        
        self.delete_btn = PushButton('删除', self)
        self.delete_btn.clicked.connect(self.deleteEmployee)
        self.delete_btn.setEnabled(False)
        bottom_bar.addWidget(self.delete_btn)
        
        bottom_bar.addStretch()
        
        self.status_label = QWidget()
        status_layout = QHBoxLayout(self.status_label)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addStretch()
        
        # 创建QLabel并设置QPixmap作为其内容
        icon_label = QLabel()
        icon_label.setPixmap(self.style().standardIcon(self.style().SP_MessageBoxInformation).pixmap(16, 16))
        status_layout.addWidget(icon_label)
        
        self.count_label = QLabel('总计: 0 名员工')
        status_layout.addWidget(self.count_label)
        
        bottom_bar.addWidget(self.status_label)
        
        main_layout.addLayout(bottom_bar)
        
        # 设置布局
        self.setLayout(main_layout)
    
    def loadEmployeeData(self, apply_filter=True):
        """加载员工数据"""
        # 保存当前列宽
        column_widths = []
        for i in range(self.model.columnCount()):
            column_widths.append(self.table_view.columnWidth(i))
        
        # 保存当前筛选条件
        current_dept = self.department_filter.currentText()
        current_grade = self.grade_filter.currentText()
        search_text = self.search_edit.text()
        
        # 清除现有数据
        self.model.removeRows(0, self.model.rowCount())
        
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
        
        # 添加员工数据到表格
        for emp in employees:
            # 获取当前年份的职级
            current_grade_emp = emp.get('grade_2024', '')
            
            # 获取备注并处理长文本
            notes = str(emp.get('notes', ''))
            truncated_notes = notes
            if len(notes) > 30:  # 限制备注显示长度为30个字符
                truncated_notes = notes[:27] + "..."
            
            # 创建表格项
            items = [
                QStandardItem(str(emp.get('id', ''))),
                QStandardItem(str(emp.get('employee_no', ''))),
                QStandardItem(str(emp.get('gid', ''))),
                QStandardItem(str(emp.get('name', ''))),
                QStandardItem(str(emp.get('department', ''))),
                QStandardItem(str(current_grade_emp)),
                QStandardItem(str(emp.get('status', ''))),
                QStandardItem(truncated_notes)
            ]
            
            # 如果备注被截断，添加工具提示显示完整内容
            if len(notes) > 30:
                items[-1].setToolTip(notes)
            
            # 设置不可编辑
            for item in items:
                item.setEditable(False)
            
            # 添加到模型
            self.model.appendRow(items)
        
        # 更新员工数量
        self.count_label.setText(f'总计: {len(employees)} 名员工')
        
        # 如果之前存在列宽设置，则恢复
        if column_widths and len(column_widths) == self.model.columnCount():
            # 恢复之前保存的列宽
            for i in range(self.model.columnCount()):
                if column_widths[i] > 0:  # 只恢复大于0的列宽
                    self.table_view.setColumnWidth(i, column_widths[i])
        else:
            # 首次加载或列数变化时，自动调整列宽
            self.table_view.resizeColumnsToContents()
        
        # 隐藏ID列
        self.table_view.hideColumn(0)
        
        # 应用筛选条件
        if apply_filter:
            # 恢复职级筛选
            if current_grade != "全部":
                self.grade_filter.setCurrentText(current_grade)
            
            # 恢复搜索文本
            if search_text:
                self.search_edit.setText(search_text)
            
            # 手动重新应用筛选
            self.filterEmployees()
    
    def refreshEmployeeList(self):
        """刷新员工列表"""
        self.loadEmployeeData(apply_filter=True)
    
    def filterEmployees(self):
        """根据搜索文本筛选员工"""
        # 获取筛选条件
        search_text = self.search_edit.text().strip()
        department = self.department_filter.currentText()
        grade = self.grade_filter.currentText()
        
        # 重置筛选，先显示所有行
        self.proxy_model.setFilterFixedString("")
        for row in range(self.model.rowCount()):
            self.table_view.showRow(row)
        
        # 应用通用搜索
        if search_text:
            self.proxy_model.setFilterFixedString(search_text)
        
        # 应用部门筛选
        if department and department != "全部":
            # 在模型中筛选指定部门
            for row in range(self.model.rowCount()):
                dept_item = self.model.item(row, 4)  # 部门列
                if dept_item and dept_item.text() != department:
                    self.table_view.hideRow(row)
                else:
                    self.table_view.showRow(row)
        
        # 应用职级筛选
        if grade and grade != "全部":
            # 在模型中筛选指定职级
            for row in range(self.model.rowCount()):
                grade_item = self.model.item(row, 5)  # 职级列
                if grade_item and grade_item.text() != grade:
                    self.table_view.hideRow(row)
                else:
                    if department and department != "全部":
                        # 如果已经应用了部门筛选，则保持其结果
                        dept_item = self.model.item(row, 4)
                        if dept_item and dept_item.text() == department:
                            self.table_view.showRow(row)
                    else:
                        self.table_view.showRow(row)
        
        # 更新显示行数
        visible_rows = 0
        for row in range(self.proxy_model.rowCount()):
            if not self.table_view.isRowHidden(row):
                visible_rows += 1
        
        self.count_label.setText(f'显示: {visible_rows} / {self.model.rowCount()} 名员工')
    
    def onTableClicked(self, index):
        """表格项被点击时触发"""
        # 启用编辑和删除按钮
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
    
    def onTableDoubleClicked(self, index):
        """表格项被双击时触发"""
        # 获取所选员工的ID
        row = index.row()
        id_index = self.proxy_model.index(row, 0)  # ID所在列
        employee_id = int(self.proxy_model.data(id_index))
        
        # 发出员工被选中的信号
        self.employeeSelected.emit(employee_id)
    
    def addEmployee(self):
        """添加新员工"""
        # 这里可以弹出添加员工的对话框
        # 暂时使用InfoBar提示
        InfoBar.info(
            title='添加员工',
            content='此功能尚未实现，将通过对话框添加员工',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
        # 后续可以实现添加员工的对话框
        # 成功添加后刷新列表
    
    def editEmployee(self):
        """编辑员工信息"""
        # 获取所选员工的ID
        indexes = self.table_view.selectedIndexes()
        if not indexes:
            return
        
        row = indexes[0].row()
        id_index = self.proxy_model.index(row, 0)  # ID所在列
        employee_id = int(self.proxy_model.data(id_index))
        
        # 这里应该打开编辑员工的界面
        self.employeeSelected.emit(employee_id)
    
    def deleteEmployee(self):
        """删除员工"""
        # 获取所选员工的ID和姓名
        indexes = self.table_view.selectedIndexes()
        if not indexes:
            return
        
        row = indexes[0].row()
        id_index = self.proxy_model.index(row, 0)  # ID所在列
        name_index = self.proxy_model.index(row, 3)  # 姓名所在列
        
        employee_id = int(self.proxy_model.data(id_index))
        employee_name = self.proxy_model.data(name_index)
        
        # 确认删除
        reply = QMessageBox.question(
            self, 
            '确认删除', 
            f'确定要删除员工 {employee_name} 吗？此操作不可撤销！',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 执行删除
            success = self.db.delete_employee(employee_id, "管理员")
            
            if success:
                InfoBar.success(
                    title='删除成功',
                    content=f"已成功删除员工 {employee_name}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                
                # 刷新列表
                self.refreshEmployeeList()
                
                # 禁用编辑和删除按钮
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
            else:
                InfoBar.error(
                    title='删除失败',
                    content="删除员工时发生错误",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                ) 
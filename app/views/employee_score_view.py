import os
import datetime
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFileDialog, QMessageBox, QLineEdit, QAbstractItemView,
    QDialog, QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox,
    QTreeWidget, QTreeWidgetItem, QSplitter, QFrame, QMenu
)
from qfluentwidgets import (
    PushButton, ComboBox, LineEdit, SpinBox, DoubleSpinBox,
    MessageBox, InfoBar, InfoBarPosition, SearchLineEdit,
    FluentIcon as FIF, TableWidget, TreeWidget, SwitchButton,
    TransparentToolButton, ToolButton, CardWidget, SimpleCardWidget,
    PrimaryPushButton, PrimaryToolButton
)

class EmployeeScoreView(QWidget):
    """员工成绩录入界面"""
    
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
        self.department_combo.currentIndexChanged.connect(self.load_employees)
        top_layout.addWidget(QLabel("部门:"))
        top_layout.addWidget(self.department_combo)
        
        # 添加年份选择下拉框
        self.year_combo = ComboBox(self)
        self.year_combo.setPlaceholderText("选择年份")
        
        # 添加年份选项（当前年份和未来4年）
        current_year = datetime.datetime.now().year
        for year in range(current_year - 1, current_year + 5):
            self.year_combo.addItem(str(year))
        
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.setMinimumWidth(100)
        top_layout.addWidget(QLabel("年份:"))
        top_layout.addWidget(self.year_combo)
        
        top_layout.addStretch(1)
        
        # 添加按钮区域
        self.import_button = PushButton("导入成绩", self, FIF.DOWNLOAD)
        self.import_button.clicked.connect(self.import_scores)
        top_layout.addWidget(self.import_button)
        
        self.export_button = PushButton("导出模板", self, FIF.SAVE)
        self.export_button.clicked.connect(self.export_template)
        top_layout.addWidget(self.export_button)
        
        self.calculate_button = PushButton("计算预测", self, FIF.ADD)
        self.calculate_button.clicked.connect(self.calculate_predicted_grades)
        top_layout.addWidget(self.calculate_button)
        
        main_layout.addLayout(top_layout)
        
        # 创建分割器和主要显示区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧员工列表
        self.employee_card = SimpleCardWidget(self)
        employee_layout = QVBoxLayout(self.employee_card)
        
        # 搜索框
        self.search_edit = SearchLineEdit(self.employee_card)
        self.search_edit.setPlaceholderText("搜索员工")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.filter_employees)
        employee_layout.addWidget(self.search_edit)
        
        # 员工树形列表
        self.employee_tree = TreeWidget(self.employee_card)
        self.employee_tree.setHeaderHidden(True)
        self.employee_tree.setIndentation(20)
        self.employee_tree.currentItemChanged.connect(self.on_employee_selected)
        employee_layout.addWidget(self.employee_tree)
        
        splitter.addWidget(self.employee_card)
        
        # 右侧成绩表格
        self.score_card = SimpleCardWidget(self)
        score_layout = QVBoxLayout(self.score_card)
        
        # 成绩表格
        self.score_table = TableWidget(self.score_card)
        self.score_table.setColumnCount(5)
        self.score_table.setHorizontalHeaderLabels(['考核项目', '权重', '满分', '得分', '备注'])
        self.score_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.score_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.score_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.score_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        
        score_layout.addWidget(self.score_table)
        
        # 保存按钮
        self.save_button = PrimaryPushButton("保存成绩", self.score_card, FIF.SAVE)
        self.save_button.clicked.connect(self.save_scores)
        score_layout.addWidget(self.save_button)
        
        splitter.addWidget(self.score_card)
        
        # 设置分割器比例
        splitter.setSizes([int(self.width() * 0.3), int(self.width() * 0.7)])
        main_layout.addWidget(splitter)
        
        # 初始状态
        self.current_employee_no = None
        self.assessment_items = []
    
    def load_departments(self):
        """加载部门列表"""
        departments = self.score_db.get_all_departments()
        for dept in departments:
            self.department_combo.addItem(dept, dept)
    
    def load_employees(self):
        """加载部门员工"""
        self.employee_tree.clear()
        self.score_table.setRowCount(0)
        self.current_employee_no = None
        
        department = self.department_combo.currentData()
        if not department:
            return
        
        employees = self.score_db.get_department_employees(department)
        
        # 创建根节点
        root = QTreeWidgetItem(self.employee_tree, [f"{department} ({len(employees)}人)"])
        
        # 添加员工
        for employee in employees:
            item = QTreeWidgetItem(root, [f"{employee['name']} ({employee['employee_no']})"])
            item.setData(0, Qt.UserRole, employee['employee_no'])
        
        self.employee_tree.expandAll()
    
    def filter_employees(self):
        """筛选员工"""
        search_text = self.search_edit.text().strip().lower()
        
        if not search_text:
            # 如果搜索框为空，显示所有员工
            for i in range(self.employee_tree.topLevelItemCount()):
                root = self.employee_tree.topLevelItem(i)
                root.setHidden(False)
                for j in range(root.childCount()):
                    root.child(j).setHidden(False)
            return
        
        # 遍历所有员工，隐藏不匹配的
        for i in range(self.employee_tree.topLevelItemCount()):
            root = self.employee_tree.topLevelItem(i)
            
            # 统计匹配的员工数量
            matched_count = 0
            
            for j in range(root.childCount()):
                employee_item = root.child(j)
                employee_text = employee_item.text(0).lower()
                
                if search_text in employee_text:
                    employee_item.setHidden(False)
                    matched_count += 1
                else:
                    employee_item.setHidden(True)
            
            # 更新根节点文本和可见性
            if matched_count > 0:
                root.setHidden(False)
                department = self.department_combo.currentData()
                root.setText(0, f"{department} ({matched_count}人)")
            else:
                root.setHidden(True)
    
    def on_employee_selected(self, current, previous):
        """员工选择改变事件"""
        if current and current.parent():  # 确保选择的是员工项而非部门项
            employee_id = current.data(0, Qt.UserRole)
            self.load_employee_scores(employee_id)
    
    def load_employee_scores(self, employee_id):
        """加载员工考核成绩"""
        # 确保year是整数
        try:
            year = int(self.year_combo.currentText())
        except ValueError:
            # 如果转换失败，使用当前年份
            year = datetime.datetime.now().year
        
        # 清空表格
        self.score_table.setRowCount(0)
        
        # 获取部门考核项目
        department = self.department_combo.currentData()
        self.assessment_items = self.score_db.get_all_assessment_items(department)
        
        # 设置员工编号 - 传入的employee_id实际上已经是employee_no
        self.current_employee_no = employee_id
        
        # 获取员工现有成绩
        employee_scores = self.score_db.get_employee_scores(employee_id, year)
        
        # 构建成绩字典，用于快速查找
        score_dict = {}
        for score in employee_scores:
            score_dict[score['assessment_item_id']] = score
        
        # 填充表格
        for row, item in enumerate(self.assessment_items):
            self.score_table.insertRow(row)
            
            # 项目名称
            name_item = QTableWidgetItem(item['assessment_name'])
            name_item.setData(Qt.UserRole, item['id'])  # 存储考核项目ID
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # 不可编辑
            self.score_table.setItem(row, 0, name_item)
            
            # 权重
            weight_item = QTableWidgetItem(str(item['weight']))
            weight_item.setFlags(weight_item.flags() & ~Qt.ItemIsEditable)  # 不可编辑
            self.score_table.setItem(row, 1, weight_item)
            
            # 满分
            max_score_item = QTableWidgetItem(str(item['max_score']))
            max_score_item.setFlags(max_score_item.flags() & ~Qt.ItemIsEditable)  # 不可编辑
            self.score_table.setItem(row, 2, max_score_item)
            
            # 得分
            score_item = QTableWidgetItem()
            if item['id'] in score_dict:
                score_item.setText(str(score_dict[item['id']]['score']))
            self.score_table.setItem(row, 3, score_item)
            
            # 备注
            comment_item = QTableWidgetItem()
            if item['id'] in score_dict:
                comment_item.setText(score_dict[item['id']]['comment'] or "")
            self.score_table.setItem(row, 4, comment_item)
    
    def save_scores(self):
        """保存员工成绩"""
        if not self.current_employee_no:
            InfoBar.error(
                title='保存失败',
                content="请先选择员工",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 收集成绩数据
        count_added = 0
        count_updated = 0
        
        # 确保year是整数
        try:
            year = int(self.year_combo.currentText())
        except ValueError:
            # 如果转换失败，使用当前年份
            year = datetime.datetime.now().year
        
        for row in range(self.score_table.rowCount()):
            assessment_item_id = self.score_table.item(row, 0).data(Qt.UserRole)
            score_text = self.score_table.item(row, 3).text().strip()
            comment = self.score_table.item(row, 4).text().strip()
            
            # 检查分数是否为空
            if not score_text:
                continue
                
            try:
                score_value = float(score_text)
            except ValueError:
                InfoBar.error(
                    title='格式错误',
                    content=f"第 {row+1} 行的分数格式错误，应为数字",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                continue
            
            # 准备成绩数据
            score_data = {
                'employee_no': self.current_employee_no,
                'assessment_year': year,
                'assessment_item_id': assessment_item_id,
                'score': score_value,
                'comment': comment
            }
            
            # 保存成绩
            success = self.score_db.save_employee_score(score_data)
            
            if success:
                # 检查是新增还是更新
                for item in self.assessment_items:
                    if item['id'] == assessment_item_id:
                        existing_scores = self.score_db.get_employee_scores(self.current_employee_no, year)
                        is_update = False
                        for existing_score in existing_scores:
                            if existing_score['assessment_item_id'] == assessment_item_id:
                                is_update = True
                                break
                        
                        if is_update:
                            count_updated += 1
                        else:
                            count_added += 1
                        break
        
        # 显示保存结果
        InfoBar.success(
            title='保存成功',
            content=f"成功保存 {count_added+count_updated} 项成绩 (新增: {count_added}, 更新: {count_updated})",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def import_scores(self):
        """导入员工成绩"""
        department = self.department_combo.currentData()
        
        # 确保year是整数
        try:
            year = int(self.year_combo.currentText())
        except ValueError:
            # 如果转换失败，使用当前年份
            year = datetime.datetime.now().year
        
        if not department:
            InfoBar.error(
                title='导入失败',
                content="请先选择部门",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "", "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        # 导入成绩
        result = self.score_db.import_employee_scores(file_path, year)
        
        if result and result.get('success'):
            # 如果导入成功
            InfoBar.success(
                title='导入成功',
                content=f"成功导入 {result.get('added')} 条新成绩, 更新 {result.get('updated')} 条成绩",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
            # 如果有错误，显示错误信息
            if result.get('errors') and len(result.get('errors')) > 0:
                error_dialog = MessageBox(
                    '导入提示',
                    f"导入过程中有 {len(result.get('errors'))} 条记录出现错误，请检查数据格式。",
                    self
                )
                error_dialog.exec()
            
            # 刷新当前显示的员工成绩
            if self.current_employee_no:
                self.load_employee_scores(self.current_employee_no)
        else:
            # 如果导入失败
            InfoBar.error(
                title='导入失败',
                content="导入成绩时出现错误，请检查文件格式",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def export_template(self):
        """导出成绩录入模板"""
        department = self.department_combo.currentData()
        
        if not department:
            InfoBar.error(
                title='导出失败',
                content="请先选择部门",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存模板文件", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            # 获取部门员工和考核项目
            employees = self.score_db.get_department_employees(department)
            assessment_items = self.score_db.get_all_assessment_items(department)
            
            # 准备模板数据
            import pandas as pd
            
            template_data = []
            
            for employee in employees:
                for item in assessment_items:
                    template_data.append({
                        'employee_no': employee['employee_no'],
                        'employee_name': employee['name'],
                        'assessment_name': item['assessment_name'],
                        'weight': item['weight'],
                        'max_score': item['max_score'],
                        'score': '',  # 留空供填写
                        'comment': ''  # 留空供填写
                    })
            
            # 创建DataFrame并导出
            df = pd.DataFrame(template_data)
            
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
                content=f"已成功导出成绩录入模板到 {file_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            InfoBar.error(
                title='导出失败',
                content=f"导出模板时出现错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def calculate_predicted_grades(self):
        """计算预测职级"""
        department = self.department_combo.currentData()
        
        # 确保year是整数
        try:
            year = int(self.year_combo.currentText())
        except ValueError:
            # 如果转换失败，使用当前年份
            year = datetime.datetime.now().year
        
        if not department:
            InfoBar.error(
                title='计算失败',
                content="请先选择部门",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 弹出确认对话框
        dialog = MessageBox(
            '确认计算',
            f"是否为 {department} 部门的所有员工计算 {year} 年的预测职级？\n\n注意：这将基于已录入的考核成绩和部门职级计算公式。",
            self
        )
        
        dialog.yesButton.setText('开始计算')
        dialog.cancelButton.setText('取消')
        
        if dialog.exec():
            # 获取部门所有员工
            employees = self.score_db.get_department_employees(department)
            
            # 计算结果统计
            success_count = 0
            fail_count = 0
            promotion_count = 0
            demotion_count = 0
            unchanged_count = 0
            
            # 遍历计算每个员工的预测职级
            for employee in employees:
                result = self.score_db.calculate_predicted_grade(employee['employee_no'], year)
                
                if result and result.get('success'):
                    success_count += 1
                    
                    # 统计晋升/降级/不变情况
                    current_grade = result.get('current_grade')
                    predicted_grade = result.get('predicted_grade')
                    
                    if current_grade == predicted_grade:
                        unchanged_count += 1
                    elif self._is_promotion(current_grade, predicted_grade):
                        promotion_count += 1
                    else:
                        demotion_count += 1
                else:
                    fail_count += 1
            
            # 显示计算结果
            if success_count > 0:
                result_message = f"成功计算 {success_count} 名员工的预测职级\n\n"
                result_message += f"晋升: {promotion_count} 人\n"
                result_message += f"降级: {demotion_count} 人\n"
                result_message += f"保持不变: {unchanged_count} 人\n"
                
                if fail_count > 0:
                    result_message += f"\n计算失败: {fail_count} 人 (可能是缺少考核成绩或公式)"
                
                result_dialog = MessageBox('计算完成', result_message, self)
                result_dialog.exec()
                
                # 如果当前有选中员工，刷新其显示
                if self.current_employee_no:
                    self.load_employee_scores(self.current_employee_no)
            else:
                InfoBar.error(
                    title='计算失败',
                    content="没有成功计算任何员工的预测职级，请确保已设置公式并录入成绩",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
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
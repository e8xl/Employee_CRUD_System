from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFileDialog, QTableWidgetItem, QHeaderView, QDialog,
    QAbstractItemView, QMessageBox, QFrame
)
from qfluentwidgets import (
    PushButton, ComboBox, InfoBar, InfoBarPosition, 
    CardWidget, TableWidget, FluentIcon, SpinBox,
    SearchLineEdit, ToolButton, setTheme, Theme, SubtitleLabel,
    LineEdit
)
import os
import datetime
import pandas as pd

class SkillScoringView(QWidget):
    """技能评分视图，用于导入和管理员工技能评分"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        
        # 初始化UI
        self.initUI()
        
    def initUI(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 顶部控制区域
        self.createControlPanel(layout)
        
        # 主要数据表格
        self.createDataTable(layout)
        
        # 加载初始数据
        self.current_year = datetime.datetime.now().year
        self.year_combo.setCurrentText(str(self.current_year))
        self.loadData()
        
    def createControlPanel(self, parent_layout):
        """创建控制面板"""
        control_card = CardWidget(self)
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_layout = QHBoxLayout()
        title = SubtitleLabel("技能评分管理", self)
        title_layout.addWidget(title)
        title_layout.addStretch(1)
        control_layout.addLayout(title_layout)
        
        # 功能按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 年份选择
        year_label = QLabel("年份:", self)
        button_layout.addWidget(year_label)
        
        self.year_combo = ComboBox(self)
        years = [str(y) for y in range(2020, datetime.datetime.now().year + 2)]
        self.year_combo.addItems(years)
        self.year_combo.currentTextChanged.connect(self.yearChanged)
        button_layout.addWidget(self.year_combo)
        
        button_layout.addStretch(1)
        
        # 搜索框
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("搜索员工...")
        self.search_edit.searchSignal.connect(self.searchEmployees)
        self.search_edit.clearSignal.connect(self.loadData)
        self.search_edit.setFixedWidth(250)
        button_layout.addWidget(self.search_edit)
        
        # 导入职级阈值按钮
        self.import_thresholds_btn = PushButton("导入职级阈值", self)
        self.import_thresholds_btn.setIcon(FluentIcon.DOWNLOAD)
        self.import_thresholds_btn.clicked.connect(self.importThresholds)
        button_layout.addWidget(self.import_thresholds_btn)
        
        # 导入成绩按钮
        self.import_scores_btn = PushButton("导入技能评分", self)
        self.import_scores_btn.setIcon(FluentIcon.DOWNLOAD)
        self.import_scores_btn.clicked.connect(self.importScores)
        button_layout.addWidget(self.import_scores_btn)
        
        # 应用到职级按钮
        self.apply_grades_btn = PushButton("应用到职级", self)
        self.apply_grades_btn.setIcon(FluentIcon.ACCEPT)
        self.apply_grades_btn.clicked.connect(self.applyGrades)
        button_layout.addWidget(self.apply_grades_btn)
        
        # 导出结果按钮
        self.export_btn = PushButton("导出结果", self)
        self.export_btn.setIcon(FluentIcon.SAVE_AS)
        self.export_btn.clicked.connect(self.exportResults)
        button_layout.addWidget(self.export_btn)
        
        control_layout.addLayout(button_layout)
        parent_layout.addWidget(control_card)
        
    def createDataTable(self, parent_layout):
        """创建数据表格"""
        # 表格容器卡片
        table_card = CardWidget(self)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建表格
        self.table = TableWidget(self)
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "ID", "工号", "GID", "姓名", "部门", "状态", 
            "基础知识", "岗位技能", "跨部门技能", "技师技能", 
            "一线管理技能", "总分", "评定职级"
        ])
        
        # 设置列宽
        self.table.setColumnWidth(0, 60)   # ID
        self.table.setColumnWidth(1, 100)  # 工号
        self.table.setColumnWidth(2, 100)  # GID
        self.table.setColumnWidth(3, 100)  # 姓名
        self.table.setColumnWidth(4, 150)  # 部门
        self.table.setColumnWidth(5, 80)   # 状态
        self.table.setColumnWidth(6, 80)   # 基础知识
        self.table.setColumnWidth(7, 80)   # 岗位技能
        self.table.setColumnWidth(8, 80)   # 跨部门技能
        self.table.setColumnWidth(9, 80)   # 技师技能
        self.table.setColumnWidth(10, 80)  # 一线管理技能
        self.table.setColumnWidth(11, 80)  # 总分
        self.table.setColumnWidth(12, 80)  # 评定职级
        
        # 设置表格属性
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # 双击打开详情
        self.table.doubleClicked.connect(self.openSkillDetails)
        
        table_layout.addWidget(self.table)
        parent_layout.addWidget(table_card)
        
    def yearChanged(self, year):
        """年份变化时重新加载数据"""
        self.current_year = int(year)
        self.loadData()
        
    def loadData(self):
        """加载技能评分数据"""
        try:
            # 查询员工和技能评分数据
            self.db.cursor.execute("""
            SELECT e.id, e.employee_no, e.gid, e.name, e.department, e.status,
                   s.basic_knowledge_score, s.position_skill_score, 
                   s.cross_department_score, s.technician_skill_score, 
                   s.management_skill_score, s.total_score, s.evaluated_grade
            FROM employees e
            LEFT JOIN skill_scores s ON e.id = s.employee_id AND s.year = ?
            ORDER BY e.department, e.name
            """, (self.current_year,))
            
            results = self.db.cursor.fetchall()
            
            # 清空表格
            self.table.setRowCount(0)
            
            # 填充数据
            for row_idx, row_data in enumerate(results):
                self.table.insertRow(row_idx)
                
                for col_idx, col_data in enumerate(row_data):
                    if col_data is None:
                        if col_idx >= 6 and col_idx <= 11:  # 分数列
                            item = QTableWidgetItem("0")
                        else:
                            item = QTableWidgetItem("")
                    else:
                        item = QTableWidgetItem(str(col_data))
                    
                    # 设置文本居中
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, col_idx, item)
        
        except Exception as e:
            print(f"加载技能评分数据失败: {e}")
            InfoBar.error(
                title='加载失败',
                content=f"加载技能评分数据失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def searchEmployees(self, keyword):
        """搜索员工"""
        if not keyword:
            self.loadData()
            return
            
        try:
            # 查询员工和技能评分数据
            search_term = f"%{keyword}%"
            self.db.cursor.execute("""
            SELECT e.id, e.employee_no, e.gid, e.name, e.department, e.status,
                   s.basic_knowledge_score, s.position_skill_score, 
                   s.cross_department_score, s.technician_skill_score, 
                   s.management_skill_score, s.total_score, s.evaluated_grade
            FROM employees e
            LEFT JOIN skill_scores s ON e.id = s.employee_id AND s.year = ?
            WHERE e.name LIKE ? OR e.employee_no LIKE ? OR e.gid LIKE ? OR e.department LIKE ?
            ORDER BY e.department, e.name
            """, (self.current_year, search_term, search_term, search_term, search_term))
            
            results = self.db.cursor.fetchall()
            
            # 清空表格
            self.table.setRowCount(0)
            
            # 填充数据
            for row_idx, row_data in enumerate(results):
                self.table.insertRow(row_idx)
                
                for col_idx, col_data in enumerate(row_data):
                    if col_data is None:
                        if col_idx >= 6 and col_idx <= 11:  # 分数列
                            item = QTableWidgetItem("0")
                        else:
                            item = QTableWidgetItem("")
                    else:
                        item = QTableWidgetItem(str(col_data))
                    
                    # 设置文本居中
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, col_idx, item)
        
        except Exception as e:
            print(f"搜索员工失败: {e}")
    
    def importScores(self):
        """导入技能评分数据"""
        try:
            # 打开文件对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择技能评分文件", "", 
                "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return
                
            # 确认导入年份
            year_dialog = ImportYearDialog(self.current_year, self)
            if year_dialog.exec_():
                import_year = year_dialog.year_spin.value()
            else:
                return
                
            # 执行导入
            result = self.db.import_skill_scores(file_path, import_year, "管理员")
            
            if result and result.get('success', False):
                # 更新当前年份并重新加载数据
                self.current_year = import_year
                self.year_combo.setCurrentText(str(import_year))
                self.loadData()
                
                # 显示成功消息
                added = result.get('added', 0)
                updated = result.get('updated', 0)
                InfoBar.success(
                    title='导入成功',
                    content=f"成功导入{added}条技能评分数据，更新{updated}条记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                # 显示错误消息
                InfoBar.error(
                    title='导入失败',
                    content="导入技能评分数据失败，请检查文件格式",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
        except Exception as e:
            print(f"导入技能评分异常: {e}")
            InfoBar.error(
                title='导入异常',
                content=f"导入过程中发生异常: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def importThresholds(self):
        """导入职级评定阈值"""
        try:
            # 打开文件对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择职级阈值文件", "", 
                "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return
                
            # 确认导入年份
            year_dialog = ImportYearDialog(self.current_year, self)
            if year_dialog.exec_():
                import_year = year_dialog.year_spin.value()
            else:
                return
                
            # 执行导入
            result = self.db.import_skill_thresholds(file_path, import_year, "管理员")
            
            if result and result.get('success', False):
                # 显示成功消息
                added = result.get('added', 0)
                InfoBar.success(
                    title='导入成功',
                    content=f"成功导入{added}条职级阈值数据",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                # 显示错误消息
                InfoBar.error(
                    title='导入失败',
                    content="导入职级阈值失败，请检查文件格式",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
        except Exception as e:
            print(f"导入职级阈值异常: {e}")
            InfoBar.error(
                title='导入异常',
                content=f"导入过程中发生异常: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def applyGrades(self):
        """应用评定的职级"""
        try:
            # 打开目标年份选择对话框
            year_dialog = TargetYearDialog(self.current_year, self)
            if year_dialog.exec_():
                target_year = year_dialog.year_spin.value()
            else:
                return
                
            # 显示确认对话框
            reply = QMessageBox.question(
                self,
                '应用职级确认',
                f"确定要将{self.current_year}年的技能评分结果应用为{target_year}年的职级吗？\n"
                f"这将更新员工信息中的{target_year}年职级字段。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 执行应用
            update_count = self.db.apply_evaluated_grades(self.current_year, target_year, "管理员")
            
            # 显示结果
            InfoBar.success(
                title='应用成功',
                content=f"成功将{self.current_year}年技能评分评定的职级应用到{target_year}年，更新了{update_count}名员工的职级",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        except Exception as e:
            print(f"应用职级异常: {e}")
            InfoBar.error(
                title='应用异常',
                content=f"应用过程中发生异常: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def exportResults(self):
        """导出评定结果"""
        try:
            # 打开保存文件对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出评定结果", f"职级评定结果_{self.current_year}.xlsx", 
                "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return
                
            # 执行导出
            result = self.db.export_evaluation_results(self.current_year, file_path, "管理员")
            
            if result:
                # 显示成功消息
                InfoBar.success(
                    title='导出成功',
                    content=f"成功导出{self.current_year}年职级评定结果",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                # 显示错误消息
                InfoBar.error(
                    title='导出失败',
                    content="导出职级评定结果失败",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
        except Exception as e:
            print(f"导出评定结果异常: {e}")
            InfoBar.error(
                title='导出异常',
                content=f"导出过程中发生异常: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def openSkillDetails(self, index):
        """打开技能详情对话框"""
        row = index.row()
        employee_id = int(self.table.item(row, 0).text())
        
        # 获取员工技能评分
        scores = self.db.get_employee_skill_scores(employee_id, self.current_year)
        if not scores:
            InfoBar.warning(
                title='无数据',
                content="未找到该员工的技能评分数据",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
            
        # 打开详情对话框
        dialog = SkillDetailDialog(self.db, employee_id, self.current_year, self)
        dialog.exec_()

class ImportYearDialog(QDialog):
    """导入年份选择对话框"""
    
    def __init__(self, default_year, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择年份")
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 年份选择
        form_layout = QHBoxLayout()
        year_label = QLabel("导入年份:", self)
        form_layout.addWidget(year_label)
        
        self.year_spin = SpinBox(self)
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(default_year)
        form_layout.addWidget(self.year_spin)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch(1)
        
        self.ok_btn = PushButton("确定", self)
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)

class TargetYearDialog(QDialog):
    """目标年份选择对话框"""
    
    def __init__(self, source_year, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择目标年份")
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 提示标签
        info_label = QLabel(f"将{source_year}年的技能评分评定结果应用为以下年份的职级:", self)
        layout.addWidget(info_label)
        
        # 年份选择
        form_layout = QHBoxLayout()
        year_label = QLabel("目标年份:", self)
        form_layout.addWidget(year_label)
        
        self.year_spin = SpinBox(self)
        self.year_spin.setRange(source_year, source_year + 5)
        self.year_spin.setValue(source_year + 1)
        form_layout.addWidget(self.year_spin)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch(1)
        
        self.ok_btn = PushButton("确定", self)
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = PushButton("取消", self)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)

class SkillDetailDialog(QDialog):
    """技能详情对话框"""
    
    def __init__(self, db, employee_id, year, parent=None):
        super().__init__(parent)
        self.db = db
        self.employee_id = employee_id
        self.year = year
        
        self.setWindowTitle("技能评分详情")
        self.resize(800, 600)
        
        self.initUI()
        self.loadData()
        
    def initUI(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 员工基本信息
        self.info_card = CardWidget(self)
        info_layout = QHBoxLayout(self.info_card)
        info_layout.setContentsMargins(20, 20, 20, 20)
        
        # 员工信息标签
        self.employee_info_label = QLabel(self)
        self.employee_info_label.setTextFormat(Qt.RichText)
        info_layout.addWidget(self.employee_info_label)
        
        # 分隔线
        separator = QFrame(self)
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        info_layout.addWidget(separator)
        
        # 评分信息
        self.score_info_label = QLabel(self)
        self.score_info_label.setTextFormat(Qt.RichText)
        info_layout.addWidget(self.score_info_label)
        
        layout.addWidget(self.info_card)
        
        # 技能详情表格
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["技能代码", "技能名称", "技能类型", "技能评分"])
        
        # 设置列宽
        self.table.setColumnWidth(0, 150)  # 技能代码
        self.table.setColumnWidth(1, 200)  # 技能名称
        self.table.setColumnWidth(2, 150)  # 技能类型
        self.table.setColumnWidth(3, 100)  # 技能评分
        
        # 设置表格属性
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.table)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.close_btn = PushButton("关闭", self)
        self.close_btn.setIcon(FluentIcon.CLOSE)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def loadData(self):
        """加载数据"""
        try:
            # 获取员工信息
            employee = self.db.get_employee_by_id(self.employee_id)
            if not employee:
                self.employee_info_label.setText("未找到员工信息")
                return
                
            # 设置员工基本信息
            self.employee_info_label.setText(
                f"<b>工号:</b> {employee.get('employee_no', '')}<br>"
                f"<b>GID:</b> {employee.get('gid', '')}<br>"
                f"<b>姓名:</b> {employee.get('name', '')}<br>"
                f"<b>部门:</b> {employee.get('department', '')}<br>"
                f"<b>状态:</b> {employee.get('status', '')}"
            )
            
            # 获取技能评分
            scores = self.db.get_employee_skill_scores(self.employee_id, self.year)
            if not scores:
                self.score_info_label.setText("未找到技能评分数据")
                return
                
            score = scores[0]
            
            # 设置评分信息
            self.score_info_label.setText(
                f"<b>评分年份:</b> {score.get('year', '')}<br>"
                f"<b>基础知识:</b> {score.get('basic_knowledge_score', 0)}<br>"
                f"<b>岗位技能:</b> {score.get('position_skill_score', 0)}<br>"
                f"<b>跨部门技能:</b> {score.get('cross_department_score', 0)}<br>"
                f"<b>技师技能:</b> {score.get('technician_skill_score', 0)}<br>"
                f"<b>一线管理技能:</b> {score.get('management_skill_score', 0)}<br>"
                f"<b>总分:</b> {score.get('total_score', 0)}<br>"
                f"<b>评定职级:</b> {score.get('evaluated_grade', '')}"
            )
            
            # 获取技能详情
            details = self.db.get_employee_skill_details(score.get('id'))
            
            # 清空表格
            self.table.setRowCount(0)
            
            # 填充技能详情
            for row_idx, detail in enumerate(details):
                self.table.insertRow(row_idx)
                
                item = QTableWidgetItem(detail.get('skill_code', ''))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 0, item)
                
                item = QTableWidgetItem(detail.get('skill_name', ''))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 1, item)
                
                item = QTableWidgetItem(detail.get('skill_type', ''))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 2, item)
                
                item = QTableWidgetItem(str(detail.get('skill_score', 0)))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 3, item)
        
        except Exception as e:
            print(f"加载技能详情失败: {e}")
            InfoBar.error(
                title='加载失败',
                content=f"加载技能详情失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            ) 
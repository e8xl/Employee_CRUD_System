import os
import datetime
import json
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QSpinBox, QDoubleSpinBox, QTabWidget, QPushButton, QMessageBox,
    QComboBox, QSplitter, QFrame, QFormLayout, QScrollArea, QAbstractItemView
)
from qfluentwidgets import (
    PrimaryPushButton, ComboBox, SearchLineEdit, TreeWidget, TableWidget,
    PushButton, SimpleCardWidget, DoubleSpinBox, InfoBar, InfoBarPosition,
    LineEdit, SpinBox, FluentIcon as FIF, CardWidget, MessageBox,
    TransparentToolButton
)

class AUTScoreView(QWidget):
    """AUT部门专用成绩录入界面"""
    
    def __init__(self, score_db, parent=None):
        super().__init__(parent)
        self.score_db = score_db
        self.current_employee_no = None
        self.assessment_items = []
        self.skill_items = []  # 岗位技能项目
        self.other_skills = []  # 其他技能项目
        # 当前年份
        self.current_year = datetime.datetime.now().year
        
        # 初始化界面
        self.initUI()
        
        # 延迟0.5秒加载数据
        QTimer.singleShot(500, self.initData)
    
    def initUI(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 8, 15, 15)
        main_layout.setSpacing(8)
        
        # 创建紧凑的顶部控制区域
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)
        
        # 部门标签 - AUT固定，使用更明显的样式
        dept_label = QLabel("AUT部门成绩录入", self)
        dept_label.setStyleSheet("font-weight: bold; color: #1976D2;")
        top_layout.addWidget(dept_label)
        
        # 评分年份 - 使用静态标签而非下拉框
        top_layout.addWidget(QLabel("评分年份:"))
        self.year_label = QLabel(str(self.current_year), self)
        self.year_label.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(self.year_label)
        
        top_layout.addStretch(1)
        
        # 员工选择
        top_layout.addWidget(QLabel("员工:"))
        self.employee_combo = ComboBox(self)
        self.employee_combo.setMinimumWidth(200)
        self.employee_combo.setPlaceholderText("选择员工")
        self.employee_combo.currentIndexChanged.connect(self.on_employee_selected)
        top_layout.addWidget(self.employee_combo)
        
        main_layout.addLayout(top_layout)
        
        # 创建主内容区域
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧: 岗位技能评分
        self.skill_table = TableWidget(self)
        self.skill_table.setColumnCount(3)
        self.skill_table.setHorizontalHeaderLabels(['考核项目', '满分', '得分'])
        self.skill_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.skill_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.skill_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 左侧卡片
        left_card = CardWidget(self)
        left_layout = QVBoxLayout(left_card)
        
        # 技能标题和一键满分按钮在同一行
        skill_header_layout = QHBoxLayout()
        
        # 更新权重说明: 普通岗位技能70%
        skill_title = QLabel("岗位技能评分 (占比70%)", left_card)
        skill_title.setStyleSheet("font-weight: bold; color: #1976D2;")
        skill_header_layout.addWidget(skill_title)
        
        # 添加一键满分按钮
        self.max_score_btn = PushButton("一键满分", left_card, FIF.ADD)
        self.max_score_btn.setToolTip("将所有技能项目设置为满分")
        self.max_score_btn.clicked.connect(self.set_all_max_score)
        skill_header_layout.addWidget(self.max_score_btn)
        
        left_layout.addLayout(skill_header_layout)
        
        # 搜索框
        self.skill_search = SearchLineEdit(left_card)
        self.skill_search.setPlaceholderText("搜索技能项目")
        self.skill_search.textChanged.connect(self.filter_skills)
        left_layout.addWidget(self.skill_search)
        
        # 技能表格
        left_layout.addWidget(self.skill_table)
        
        # 总分显示
        self.total_score_label = QLabel("当前总分: 0分", left_card)
        self.total_score_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #1976D2; padding: 5px;")
        left_layout.addWidget(self.total_score_label)
        
        # 手焊单独显示
        hand_solder_box = QGroupBox("手焊技能评分 (占比10%)", left_card)
        hand_solder_layout = QHBoxLayout(hand_solder_box)
        
        hand_solder_layout.addWidget(QLabel("手焊:"))
        self.hand_solder_spin = DoubleSpinBox(hand_solder_box)
        self.hand_solder_spin.setRange(0, 10)
        self.hand_solder_spin.setSingleStep(0.5)
        self.hand_solder_spin.setDecimals(1)
        self.hand_solder_spin.valueChanged.connect(self.update_total_score)
        hand_solder_layout.addWidget(self.hand_solder_spin)
        
        hand_solder_layout.addWidget(QLabel("满分10分"))
        hand_solder_layout.addStretch(1)
        
        left_layout.addWidget(hand_solder_box)
        
        # 添加制度要求比例
        requirement_box = QGroupBox("制度要求比例", left_card)
        requirement_layout = QHBoxLayout(requirement_box)
        
        requirement_layout.addWidget(QLabel("比例:"))
        self.requirement_spin = DoubleSpinBox(requirement_box)
        self.requirement_spin.setRange(0, 100)
        self.requirement_spin.setSingleStep(5)
        self.requirement_spin.setDecimals(1)
        self.requirement_spin.setSuffix("%")
        self.requirement_spin.valueChanged.connect(self.update_total_score)
        self.requirement_spin.setToolTip("制度要求比例是指员工因违反公司制度被扣分的比例，影响最终职级评定")
        requirement_layout.addWidget(self.requirement_spin)
        
        info_btn = TransparentToolButton(FIF.INFO, requirement_box)
        info_btn.setToolTip("制度要求比例是指员工因违反公司制度被扣分的比例，该比例越高表示违规情况越严重，对最终职级评定有重要影响")
        info_btn.clicked.connect(self.show_requirement_help)
        requirement_layout.addWidget(info_btn)
        
        requirement_layout.addStretch(1)
        
        left_layout.addWidget(requirement_box)
        
        content_splitter.addWidget(left_card)
        
        # 右侧: 其他技能评分和结果显示
        right_card = CardWidget(self)
        right_layout = QVBoxLayout(right_card)
        
        # 其他技能表单
        other_skills_box = QGroupBox("其他技能评分", right_card)
        skills_form = QFormLayout(other_skills_box)
        
        # 通用技能 (20%)
        self.general_skill_spin = DoubleSpinBox(other_skills_box)
        self.general_skill_spin.setRange(0, 20)
        self.general_skill_spin.setSingleStep(0.5)
        self.general_skill_spin.setDecimals(1)
        self.general_skill_spin.valueChanged.connect(self.update_total_score)
        skills_form.addRow("通用技能 (20%):", self.general_skill_spin)
        
        # 添加跨车间技能 (10%)
        self.cross_dept_skill_spin = DoubleSpinBox(other_skills_box)
        self.cross_dept_skill_spin.setRange(0, 10)
        self.cross_dept_skill_spin.setSingleStep(0.5)
        self.cross_dept_skill_spin.setDecimals(1)
        self.cross_dept_skill_spin.valueChanged.connect(self.update_total_score)
        skills_form.addRow("跨车间技能 (10%):", self.cross_dept_skill_spin)
        
        # 添加技师技能 (10%)
        self.technician_skill_spin = DoubleSpinBox(other_skills_box)
        self.technician_skill_spin.setRange(0, 10)
        self.technician_skill_spin.setSingleStep(0.5)
        self.technician_skill_spin.setDecimals(1)
        self.technician_skill_spin.valueChanged.connect(self.update_total_score)
        skills_form.addRow("技师技能 (10%):", self.technician_skill_spin)
        
        # 添加一线管理技能 (10%)
        self.management_skill_spin = DoubleSpinBox(other_skills_box)
        self.management_skill_spin.setRange(0, 10)
        self.management_skill_spin.setSingleStep(0.5)
        self.management_skill_spin.setDecimals(1)
        self.management_skill_spin.valueChanged.connect(self.update_total_score)
        skills_form.addRow("一线管理技能 (10%):", self.management_skill_spin)
        
        right_layout.addWidget(other_skills_box)
        
        # 结果显示区域
        results_box = QGroupBox("计算结果", right_card)
        results_layout = QVBoxLayout(results_box)
        
        self.skill_score_label = QLabel("岗位技能得分: 0分 (0%)", results_box)
        self.skill_score_label.setStyleSheet("font-weight: bold;")
        results_layout.addWidget(self.skill_score_label)
        
        self.hand_solder_label = QLabel("手焊技能得分: 0/10分 (0%)", results_box)
        results_layout.addWidget(self.hand_solder_label)
        
        self.general_skill_label = QLabel("通用技能得分: 0/20分 (0%)", results_box)
        results_layout.addWidget(self.general_skill_label)
        
        self.cross_dept_skill_label = QLabel("跨车间技能得分: 0/10分 (0%)", results_box)
        results_layout.addWidget(self.cross_dept_skill_label)
        
        self.technician_skill_label = QLabel("技师技能得分: 0/10分 (0%)", results_box)
        results_layout.addWidget(self.technician_skill_label)
        
        self.management_skill_label = QLabel("一线管理技能得分: 0/10分 (0%)", results_box)
        results_layout.addWidget(self.management_skill_label)
        
        # 添加制度要求比例显示
        self.requirement_label = QLabel("制度要求比例: 0%", results_box)
        self.requirement_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        results_layout.addWidget(self.requirement_label)
        
        # 添加岗位技能系数
        self.skill_coefficient_label = QLabel("岗位技能系数: 0%", results_box)
        self.skill_coefficient_label.setStyleSheet("font-weight: bold;")
        results_layout.addWidget(self.skill_coefficient_label)
        
        # 添加总分标签
        self.weighted_total_label = QLabel("总评分: 0/130分 (0%)", results_box)
        self.weighted_total_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #1976D2;")
        results_layout.addWidget(self.weighted_total_label)
        
        self.predicted_grade_label = QLabel("预测职级: 未评定", results_box)
        self.predicted_grade_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        results_layout.addWidget(self.predicted_grade_label)
        
        right_layout.addWidget(results_box)
        
        # 计算按钮
        calculate_layout = QHBoxLayout()
        
        self.calculate_btn = PrimaryPushButton("计算职级", right_card, FIF.FONT_SIZE)
        self.calculate_btn.clicked.connect(self.calculate_grade)
        calculate_layout.addWidget(self.calculate_btn)
        
        right_layout.addLayout(calculate_layout)
        
        # 保存按钮
        self.save_btn = PrimaryPushButton("保存评分", right_card, FIF.SAVE)
        self.save_btn.clicked.connect(self.save_scores)
        right_layout.addWidget(self.save_btn)
        
        content_splitter.addWidget(right_card)
        
        # 设置分割比例
        content_splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        main_layout.addWidget(content_splitter)
    
    def initData(self):
        """初始化数据 - 加载员工和考核项目"""
        # 加载AUT部门员工
        self.load_employees()
        
        # 加载考核项目
        self.load_assessment_items()
    
    def load_employees(self):
        """加载AUT部门员工"""
        self.employee_combo.clear()
        self.employee_combo.addItem("请选择员工", None)
        
        try:
            # 获取AUT部门所有员工
            self.score_db.cursor.execute(
                "SELECT employee_no, name FROM employees WHERE department = 'AUT' ORDER BY name"
            )
            employees = self.score_db.cursor.fetchall()
            
            for emp_no, name in employees:
                self.employee_combo.addItem(f"{name} ({emp_no})", emp_no)
                
            print(f"成功加载AUT部门员工: {len(employees)}人")
        except Exception as e:
            print(f"加载员工失败: {e}")
    
    def load_assessment_items(self):
        """加载AUT部门考核项目"""
        try:
            # 获取岗位技能项目
            self.score_db.cursor.execute("""
            SELECT id, assessment_name, max_score, category 
            FROM department_assessment_items 
            WHERE department = 'AUT' AND category = '岗位技能'
            ORDER BY assessment_name
            """)
            self.skill_items = self.score_db.cursor.fetchall()
            
            # 获取手焊项目
            self.score_db.cursor.execute("""
            SELECT id, assessment_name, max_score 
            FROM department_assessment_items 
            WHERE department = 'AUT' AND category = '手焊技能'
            """)
            self.hand_solder_item = self.score_db.cursor.fetchone()
            
            # 获取其他技能项目
            self.score_db.cursor.execute("""
            SELECT id, assessment_name, max_score, category 
            FROM department_assessment_items 
            WHERE department = 'AUT' AND category IN ('通用技能', '跨车间技能', '技师技能', '管理技能')
            """)
            self.other_skills = self.score_db.cursor.fetchall()
            
            # 填充岗位技能表格
            self.skill_table.setRowCount(len(self.skill_items))
            for row, (item_id, name, max_score, category) in enumerate(self.skill_items):
                # 项目名称
                name_item = QTableWidgetItem(name)
                name_item.setData(Qt.UserRole, item_id)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.skill_table.setItem(row, 0, name_item)
                
                # 满分
                max_score_item = QTableWidgetItem(str(max_score))
                max_score_item.setFlags(max_score_item.flags() & ~Qt.ItemIsEditable)
                self.skill_table.setItem(row, 1, max_score_item)
                
                # 得分 - 使用DoubleSpinBox
                score_spin = DoubleSpinBox()
                score_spin.setRange(0, max_score)
                score_spin.setSingleStep(0.5)
                score_spin.setDecimals(1)
                score_spin.valueChanged.connect(self.update_total_score)
                self.skill_table.setCellWidget(row, 2, score_spin)
            
            # 调整表格尺寸
            self.skill_table.resizeColumnsToContents()
            self.skill_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            
            print(f"成功加载岗位技能项目: {len(self.skill_items)}个")
            print(f"成功加载其他技能项目: {len(self.other_skills)}个")
            if self.hand_solder_item:
                print(f"成功加载手焊技能项目: {self.hand_solder_item[1]}")
            
        except Exception as e:
            print(f"加载考核项目失败: {e}")
            import traceback
            traceback.print_exc()
    
    def filter_skills(self):
        """筛选技能项目"""
        search_text = self.skill_search.text().lower()
        
        for row in range(self.skill_table.rowCount()):
            item = self.skill_table.item(row, 0)
            if not item:
                continue
                
            if search_text and search_text not in item.text().lower():
                self.skill_table.hideRow(row)
            else:
                self.skill_table.showRow(row)
    
    def on_employee_selected(self):
        """员工选择变化处理"""
        emp_no = self.employee_combo.currentData()
        
        if not emp_no:
            self.current_employee_no = None
            return
            
        self.current_employee_no = emp_no
        self.load_scores()
        
        # 确认当前员工已选中
        InfoBar.success(
            title='已选择员工',
            content=f'当前选择: {self.employee_combo.currentText()}',
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )
    
    def load_scores(self):
        """加载员工成绩"""
        if not self.current_employee_no:
            return
            
        try:
            year = int(self.year_label.text())
            
            # 清空所有得分
            self.clear_scores()
            
            # 获取员工所有成绩
            self.score_db.cursor.execute("""
            SELECT s.assessment_item_id, s.score, a.category, s.comment
            FROM employee_scores s
            JOIN department_assessment_items a ON s.assessment_item_id = a.id
            WHERE s.employee_no = ? AND s.assessment_year = ?
            """, (self.current_employee_no, year))
            
            scores = self.score_db.cursor.fetchall()
            
            # 设置各项目得分
            for item_id, score, category, comment in scores:
                if category == '岗位技能':
                    self.set_skill_score(item_id, score)
                elif category == '手焊技能' and self.hand_solder_item and item_id == self.hand_solder_item[0]:
                    self.hand_solder_spin.setValue(score)
                elif category == '通用技能':
                    self.general_skill_spin.setValue(score)
                elif category == '跨车间技能':
                    self.cross_dept_skill_spin.setValue(score)
                elif category == '技师技能':
                    self.technician_skill_spin.setValue(score)
                elif category == '管理技能':
                    self.management_skill_spin.setValue(score)
                # 加载制度要求比例
                elif category == '制度要求':
                    self.requirement_spin.setValue(score)
            
            # 查询是否有预测结果，如果有则获取制度要求比例
            self.score_db.cursor.execute("""
            SELECT calculation_details FROM predicted_grades
            WHERE employee_no = ? AND assessment_year = ?
            """, (self.current_employee_no, year))
            
            pred_result = self.score_db.cursor.fetchone()
            if pred_result and pred_result[0]:
                try:
                    calc_details = json.loads(pred_result[0])
                    if 'requirement_ratio' in calc_details:
                        self.requirement_spin.setValue(calc_details['requirement_ratio'])
                except Exception as e:
                    print(f"解析计算详情失败: {e}")
            
            # 立即计算职级
            self.calculate_grade()
            
            InfoBar.success(
                title='成功',
                content=f'已加载员工{self.employee_combo.currentText()}的{year}年评分',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            
        except Exception as e:
            print(f"加载成绩失败: {e}")
            InfoBar.error(
                title='错误',
                content=f'加载成绩失败: {str(e)}',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def set_skill_score(self, item_id, score):
        """设置岗位技能得分"""
        for row in range(self.skill_table.rowCount()):
            item = self.skill_table.item(row, 0)
            if not item:
                continue
            
            if item.data(Qt.UserRole) == item_id:
                spin = self.skill_table.cellWidget(row, 2)
                if spin:
                    spin.setValue(score)
                break
    
    def clear_scores(self):
        """清空所有得分"""
        # 清空岗位技能得分
        for row in range(self.skill_table.rowCount()):
            spin = self.skill_table.cellWidget(row, 2)
            if spin:
                spin.setValue(0)
                
        # 清空手焊技能得分
        self.hand_solder_spin.setValue(0)
        
        # 清空其他技能得分
        self.general_skill_spin.setValue(0)
        self.cross_dept_skill_spin.setValue(0)
        self.technician_skill_spin.setValue(0)
        self.management_skill_spin.setValue(0)
        
        # 清空制度要求比例
        self.requirement_spin.setValue(0)
        
        # 清空结果显示
        self.skill_score_label.setText("岗位技能得分: 0分 (0%)")
        self.hand_solder_label.setText("手焊技能得分: 0/10分 (0%)")
        self.general_skill_label.setText("通用技能得分: 0/20分 (0%)")
        self.cross_dept_skill_label.setText("跨车间技能得分: 0/10分 (0%)")
        self.technician_skill_label.setText("技师技能得分: 0/10分 (0%)")
        self.management_skill_label.setText("一线管理技能得分: 0/10分 (0%)")
        self.requirement_label.setText("制度要求比例: 0%")
        self.skill_coefficient_label.setText("岗位技能系数: 0%")
        self.weighted_total_label.setText("总评分: 0/130分 (0%)")
        self.predicted_grade_label.setText("预测职级: 未评定")
        
        # 更新总分显示
        self.total_score_label.setText("当前总分: 0分")
    
    def calculate_grade(self):
        """计算职级"""
        # 如果current_employee_no为None但界面已选择员工，则重新获取员工编号
        if not self.current_employee_no and self.employee_combo.currentIndex() > 0:
            # 尝试从界面获取员工编号
            emp_no = self.employee_combo.currentData()
            selected_text = self.employee_combo.currentText()
            
            # 如果currentData返回None，尝试从文本解析
            if not emp_no and '(' in selected_text and ')' in selected_text:
                try:
                    emp_no = selected_text.split("(")[1].strip(")")
                    print(f"【计算职级】从文本解析的员工编号: {emp_no}")
                    self.current_employee_no = emp_no
                except Exception as e:
                    print(f"【计算职级】解析员工编号失败: {e}")
            else:
                self.current_employee_no = emp_no
                
            print(f"【计算职级】设置员工编号: {self.current_employee_no}")
            
        if not self.current_employee_no:
            InfoBar.warning(
                title='警告',
                content='请先选择员工',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
            
        try:
            # 计算岗位技能得分
            skill_score = 0
            for row in range(self.skill_table.rowCount()):
                spin = self.skill_table.cellWidget(row, 2)
                if spin:
                    skill_score += spin.value()
            
            # 计算岗位技能系数 (百分比)
            skill_coefficient = skill_score / 70 * 100 if skill_score > 0 else 0
            self.skill_score_label.setText(f"岗位技能得分: {skill_score:.1f}分 ({skill_coefficient:.1f}%)")
            self.skill_coefficient_label.setText(f"岗位技能系数: {skill_coefficient:.1f}%")
            
            # 获取制度要求比例
            requirement_ratio = self.requirement_spin.value()
            self.requirement_label.setText(f"制度要求比例: {requirement_ratio:.1f}%")
            
            # 手焊技能得分 (占10%)
            hand_solder_score = self.hand_solder_spin.value()
            hand_solder_percentage = hand_solder_score / 10 * 100 if hand_solder_score > 0 else 0
            self.hand_solder_label.setText(f"手焊技能得分: {hand_solder_score:.1f}/10分 ({hand_solder_percentage:.1f}%)")
            
            # 通用技能得分 (占20%)
            general_score = self.general_skill_spin.value()
            general_percentage = general_score / 20 * 100 if general_score > 0 else 0
            self.general_skill_label.setText(f"通用技能得分: {general_score:.1f}/20分 ({general_percentage:.1f}%)")
            
            # 跨车间技能得分 (占10%)
            cross_dept_score = self.cross_dept_skill_spin.value()
            cross_dept_percentage = cross_dept_score / 10 * 100 if cross_dept_score > 0 else 0
            self.cross_dept_skill_label.setText(f"跨车间技能得分: {cross_dept_score:.1f}/10分 ({cross_dept_percentage:.1f}%)")
            
            # 技师技能得分 (占10%)
            technician_score = self.technician_skill_spin.value()
            technician_percentage = technician_score / 10 * 100 if technician_score > 0 else 0
            self.technician_skill_label.setText(f"技师技能得分: {technician_score:.1f}/10分 ({technician_percentage:.1f}%)")
            
            # 一线管理技能得分 (占10%)
            management_score = self.management_skill_spin.value()
            management_percentage = management_score / 10 * 100 if management_score > 0 else 0
            self.management_skill_label.setText(f"一线管理技能得分: {management_score:.1f}/10分 ({management_percentage:.1f}%)")
            
            # 计算总分 (130分)
            total_score = skill_score + hand_solder_score + general_score + cross_dept_score + technician_score + management_score
            total_percentage = total_score / 130 * 100 if total_score > 0 else 0
            
            # 更新总分标签
            self.weighted_total_label.setText(f"总评分: {total_score:.1f}/130分 ({total_percentage:.1f}%)")
            
            # 根据岗位技能系数和制度要求比例确定职级
            predicted_grade = self.determine_grade(skill_coefficient, requirement_ratio)
            self.predicted_grade_label.setText(f"预测职级: {predicted_grade}")
            
            # 更新界面样式
            if predicted_grade == "G4B":
                self.predicted_grade_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2e7d32;")
            elif predicted_grade == "G4A":
                self.predicted_grade_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
            elif predicted_grade == "G3":
                self.predicted_grade_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #0277BD;")
            elif predicted_grade == "G2":
                self.predicted_grade_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F57C00;")
            elif predicted_grade == "G1":
                self.predicted_grade_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
            else:
                self.predicted_grade_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
            
            # 获取员工当前职级
            self.score_db.cursor.execute(
                "SELECT grade_2024, grade_2023 FROM employees WHERE employee_no = ?", 
                (self.current_employee_no,)
            )
            grades = self.score_db.cursor.fetchone()
            current_grade = grades[0] if grades[0] else (grades[1] if grades[1] else "未知")
            
            # 构建计算详情
            calculation_details = {
                'scores': [
                    {'item': '岗位技能', 'raw_score': skill_score, 'max_score': 70, 'weight': 0.7},
                    {'item': '手焊技能', 'raw_score': hand_solder_score, 'max_score': 10, 'weight': 0.1},
                    {'item': '通用技能', 'raw_score': general_score, 'max_score': 20, 'weight': 0.2},
                    {'item': '跨车间技能', 'raw_score': cross_dept_score, 'max_score': 10, 'weight': 0.1},
                    {'item': '技师技能', 'raw_score': technician_score, 'max_score': 10, 'weight': 0.1},
                    {'item': '管理技能', 'raw_score': management_score, 'max_score': 10, 'weight': 0.1}
                ],
                'total_score': total_score,
                'total_percentage': total_percentage,
                'skill_coefficient': skill_coefficient,
                'requirement_ratio': requirement_ratio,
                'predicted_grade': predicted_grade
            }
            
            year = int(self.year_label.text())
            
            # 保存预测结果
            self.score_db.cursor.execute('''
            INSERT OR REPLACE INTO predicted_grades (
                employee_no, assessment_year, current_grade, 
                predicted_grade, total_score, calculation_details
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.current_employee_no,
                year,
                current_grade,
                predicted_grade,
                total_score,
                json.dumps(calculation_details)
            ))
            
            self.score_db.conn.commit()
            
            return predicted_grade
            
        except Exception as e:
            print(f"计算职级失败: {e}")
            import traceback
            traceback.print_exc()
            InfoBar.error(
                title='错误',
                content=f'计算职级失败: {str(e)}',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return "未评定"
    
    def determine_grade(self, skill_coefficient, requirement_ratio):
        """根据岗位技能系数和制度要求比例确定职级"""
        # G4B门槛: 岗位技能系数≥90%, 制度要求比例0~5%
        if skill_coefficient >= 90 and 0 <= requirement_ratio <= 5:
            return "G4B"
        # G4A门槛: 岗位技能系数≥80%, 制度要求比例10%~20%
        elif skill_coefficient >= 80 and 10 <= requirement_ratio <= 20:
            return "G4A"
        # G3门槛: 岗位技能系数≥50%, 制度要求比例40%~50%
        elif skill_coefficient >= 50 and 40 <= requirement_ratio <= 50:
            return "G3"
        # G2门槛: 岗位技能系数≥30%, 制度要求比例20%~40%
        elif skill_coefficient >= 30 and 20 <= requirement_ratio <= 40:
            return "G2"
        # G1门槛: 无特定要求
        else:
            return "G1"
    
    def save_scores(self):
        """保存评分"""
        # 如果current_employee_no为None但界面已选择员工，则重新获取员工编号
        if not self.current_employee_no and self.employee_combo.currentIndex() > 0:
            # 尝试从界面获取员工编号
            emp_no = self.employee_combo.currentData()
            selected_text = self.employee_combo.currentText()
            
            # 如果currentData返回None，尝试从文本解析
            if not emp_no and '(' in selected_text and ')' in selected_text:
                try:
                    emp_no = selected_text.split("(")[1].strip(")")
                    print(f"【计算职级】从文本解析的员工编号: {emp_no}")
                    self.current_employee_no = emp_no
                except Exception as e:
                    print(f"【计算职级】解析员工编号失败: {e}")
            else:
                self.current_employee_no = emp_no
                
            print(f"【计算职级】设置员工编号: {self.current_employee_no}")
            
        if not self.current_employee_no:
            InfoBar.warning(
                title='警告',
                content='请先选择员工',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
        
        try:
            year = int(self.year_label.text())
            saved_items = 0
            
            # 保存岗位技能得分
            for row in range(self.skill_table.rowCount()):
                item = self.skill_table.item(row, 0)
                spin = self.skill_table.cellWidget(row, 2)
                
                if item and spin:
                    item_id = item.data(Qt.UserRole)
                    score = spin.value()
                    
                    score_data = {
                        'employee_no': self.current_employee_no,
                        'assessment_year': year,
                        'assessment_item_id': item_id,
                        'score': score,
                        'comment': ''
                    }
                    
                    if self.score_db.save_employee_score(score_data):
                        saved_items += 1
            
            # 保存手焊技能得分
            if self.hand_solder_item:
                hand_solder_score = {
                    'employee_no': self.current_employee_no,
                    'assessment_year': year,
                    'assessment_item_id': self.hand_solder_item[0],
                    'score': self.hand_solder_spin.value(),
                    'comment': ''
                }
                
                if self.score_db.save_employee_score(hand_solder_score):
                    saved_items += 1
            
            # 获取并保存其他技能得分
            for skill in self.other_skills:
                item_id = skill[0]
                category = skill[3]
                
                if category == '通用技能':
                    score = self.general_skill_spin.value()
                elif category == '跨车间技能':
                    score = self.cross_dept_skill_spin.value()
                elif category == '技师技能':
                    score = self.technician_skill_spin.value()
                elif category == '管理技能':
                    score = self.management_skill_spin.value()
                else:
                    continue
                
                score_data = {
                    'employee_no': self.current_employee_no,
                    'assessment_year': year,
                    'assessment_item_id': item_id,
                    'score': score,
                    'comment': ''
                }
                
                if self.score_db.save_employee_score(score_data):
                    saved_items += 1
            
            # 保存制度要求比例
            # 先检查是否存在制度要求项目
            self.score_db.cursor.execute("""
            SELECT id FROM department_assessment_items 
            WHERE department = 'AUT' AND category = '制度要求'
            LIMIT 1
            """)
            requirement_item = self.score_db.cursor.fetchone()
            
            # 如果不存在，创建一个
            if not requirement_item:
                self.score_db.cursor.execute("""
                INSERT INTO department_assessment_items (
                    department, assessment_name, category, max_score
                ) VALUES (?, ?, ?, ?)
                """, ('AUT', '制度要求比例', '制度要求', 100))
                self.score_db.conn.commit()
                
                self.score_db.cursor.execute("SELECT last_insert_rowid()")
                requirement_item_id = self.score_db.cursor.fetchone()[0]
            else:
                requirement_item_id = requirement_item[0]
            
            # 保存制度要求比例
            requirement_score = {
                'employee_no': self.current_employee_no,
                'assessment_year': year,
                'assessment_item_id': requirement_item_id,
                'score': self.requirement_spin.value(),
                'comment': '制度要求比例'
            }
            
            if self.score_db.save_employee_score(requirement_score):
                saved_items += 1
            
            # 计算并保存总分
            # 计算岗位技能得分
            skill_score = 0
            for row in range(self.skill_table.rowCount()):
                spin = self.skill_table.cellWidget(row, 2)
                if spin:
                    skill_score += spin.value()
            
            # 计算岗位技能系数
            skill_coefficient = skill_score / 70 * 100 if skill_score > 0 else 0
            
            # 获取制度要求比例
            requirement_ratio = self.requirement_spin.value()
            
            # 手焊技能得分
            hand_solder_score = self.hand_solder_spin.value()
            
            # 其他技能得分
            general_score = self.general_skill_spin.value()
            cross_dept_score = self.cross_dept_skill_spin.value()
            technician_score = self.technician_skill_spin.value()
            management_score = self.management_skill_spin.value()
            
            # 计算总分
            total_score = skill_score + hand_solder_score + general_score + cross_dept_score + technician_score + management_score
            total_percentage = total_score / 130 * 100 if total_score > 0 else 0
            
            # 计算预测职级
            predicted_grade = self.determine_grade(skill_coefficient, requirement_ratio)
            
            # 获取员工当前职级
            self.score_db.cursor.execute(
                "SELECT grade_2024, grade_2023 FROM employees WHERE employee_no = ?", 
                (self.current_employee_no,)
            )
            grades = self.score_db.cursor.fetchone()
            current_grade = grades[0] if grades[0] else (grades[1] if grades[1] else "未知")
            
            # 构建计算详情
            calculation_details = {
                'scores': [
                    {'item': '岗位技能', 'raw_score': skill_score, 'max_score': 70, 'weight': 0.7},
                    {'item': '手焊技能', 'raw_score': hand_solder_score, 'max_score': 10, 'weight': 0.1},
                    {'item': '通用技能', 'raw_score': general_score, 'max_score': 20, 'weight': 0.2},
                    {'item': '跨车间技能', 'raw_score': cross_dept_score, 'max_score': 10, 'weight': 0.1},
                    {'item': '技师技能', 'raw_score': technician_score, 'max_score': 10, 'weight': 0.1},
                    {'item': '管理技能', 'raw_score': management_score, 'max_score': 10, 'weight': 0.1}
                ],
                'total_score': total_score,
                'total_percentage': total_percentage,
                'skill_coefficient': skill_coefficient,
                'requirement_ratio': requirement_ratio,
                'predicted_grade': predicted_grade
            }
            
            # 保存预测结果
            self.score_db.cursor.execute('''
            INSERT OR REPLACE INTO predicted_grades (
                employee_no, assessment_year, current_grade, 
                predicted_grade, total_score, calculation_details
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.current_employee_no,
                year,
                current_grade,
                predicted_grade,
                total_score,
                json.dumps(calculation_details)
            ))
            
            self.score_db.conn.commit()
            
            # 更新员工表的职级字段
            grade_field = f"grade_{year}"
            self.score_db.cursor.execute(f"""
            UPDATE employees SET {grade_field} = ? WHERE employee_no = ?
            """, (predicted_grade, self.current_employee_no))
            self.score_db.conn.commit()
            
            # 记录操作日志
            employee_name = self.employee_combo.currentText().split(" (")[0]
            self.score_db.cursor.execute('''
            INSERT INTO operation_logs (user, operation, details, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                "系统",
                "保存员工成绩",
                f"保存员工 {employee_name} {year}年AUT成绩，共{saved_items}项，预测职级: {predicted_grade}，总分: {total_score:.1f}，岗位技能系数: {skill_coefficient:.1f}%，制度要求比例: {requirement_ratio:.1f}%"
            ))
            
            self.score_db.conn.commit()
            
            InfoBar.success(
                title='保存成功',
                content=f'已保存员工{employee_name}的{year}年评分，共{saved_items}项，总分: {total_score:.1f}，预测职级: {predicted_grade}',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            
        except Exception as e:
            print(f"保存成绩失败: {e}")
            import traceback
            traceback.print_exc()
            InfoBar.error(
                title='错误',
                content=f'保存成绩失败: {str(e)}',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def refresh_scores(self):
        """刷新成绩"""
        if self.current_employee_no:
            self.load_scores() 

    def set_all_max_score(self):
        """将所有技能项目设置为满分"""
        for row in range(self.skill_table.rowCount()):
            spin = self.skill_table.cellWidget(row, 2)
            if spin:
                spin.setValue(spin.maximum())
        self.update_total_score()

    def update_total_score(self):
        """更新总分"""
        # 计算岗位技能得分
        skill_score = 0
        for row in range(self.skill_table.rowCount()):
            spin = self.skill_table.cellWidget(row, 2)
            if spin:
                skill_score += spin.value()
        
        # 获取其他技能得分
        hand_solder_score = self.hand_solder_spin.value()
        general_score = self.general_skill_spin.value()
        cross_dept_score = self.cross_dept_skill_spin.value()
        technician_score = self.technician_skill_spin.value()
        management_score = self.management_skill_spin.value()
        
        # 计算总分
        total_score = skill_score + hand_solder_score + general_score + cross_dept_score + technician_score + management_score
        
        # 更新总分显示
        self.total_score_label.setText(f"当前总分: {total_score:.1f}分")

    def show_requirement_help(self):
        """显示制度要求比例的说明"""
        InfoBar.info(
            title='制度要求比例说明',
            content="制度要求比例是指员工因违反公司制度被扣分的比例，\n该比例越高表示违规情况越严重，\n对最终职级评定有重要影响。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=5000
        ) 
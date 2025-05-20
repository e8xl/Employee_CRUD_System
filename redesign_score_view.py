#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QSpinBox, QDoubleSpinBox, QTabWidget, QPushButton, QMessageBox,
    QComboBox, QSplitter, QFrame, QFormLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QColor
from qfluentwidgets import (
    PrimaryPushButton, ComboBox, SearchLineEdit, TreeWidget, TableWidget,
    PushButton, SimpleCardWidget, DoubleSpinBox, InfoBar, InfoBarPosition,
    LineEdit, SpinBox, FluentIcon as FIF
)

def redesign_score_view():
    """重新设计AUT部门成绩录入界面，使其符合新的计算逻辑"""
    # 连接数据库
    print("正在连接数据库...")
    conn = sqlite3.connect('employee_db.sqlite')
    cursor = conn.cursor()
    
    # 修改视图类
    new_view_code = """
import os
import datetime
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
    LineEdit, SpinBox, FluentIcon as FIF, CardWidget, MessageBox
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
        
        # 初始化界面
        self.initUI()
        
        # 延迟0.5秒加载数据
        QTimer.singleShot(500, self.initData)
    
    def initUI(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 20)
        main_layout.setSpacing(10)
        
        # 顶部说明
        guide_label = QLabel("AUT部门员工成绩录入 (依据岗位技能系数和制度要求比例计算职级)", self)
        guide_label.setStyleSheet(
            "QLabel { background-color: #E3F2FD; padding: 8px; border-radius: 4px; font-weight: bold; }"
        )
        main_layout.addWidget(guide_label)
        
        # 顶部控制区域
        top_layout = QHBoxLayout()
        
        # 部门标签 - AUT固定
        dept_label = QLabel("部门: AUT", self)
        dept_label.setMinimumWidth(100)
        top_layout.addWidget(dept_label)
        
        # 年份选择
        self.year_combo = ComboBox(self)
        self.year_combo.setMinimumWidth(100)
        current_year = datetime.datetime.now().year
        for year in range(current_year - 1, current_year + 5):
            self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentIndexChanged.connect(self.refresh_scores)
        
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("评分年份:"))
        year_layout.addWidget(self.year_combo)
        top_layout.addLayout(year_layout)
        
        top_layout.addStretch(1)
        
        # 员工选择
        self.employee_combo = ComboBox(self)
        self.employee_combo.setMinimumWidth(200)
        self.employee_combo.setPlaceholderText("选择员工")
        self.employee_combo.currentIndexChanged.connect(self.on_employee_selected)
        
        employee_layout = QHBoxLayout()
        employee_layout.addWidget(QLabel("员工:"))
        employee_layout.addWidget(self.employee_combo)
        top_layout.addLayout(employee_layout)
        
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
        
        skill_title = QLabel("岗位技能评分 (总分204分，占比60%)", left_card)
        skill_title.setStyleSheet("font-weight: bold; color: #1976D2;")
        left_layout.addWidget(skill_title)
        
        # 搜索框
        self.skill_search = SearchLineEdit(left_card)
        self.skill_search.setPlaceholderText("搜索技能项目")
        self.skill_search.textChanged.connect(self.filter_skills)
        left_layout.addWidget(self.skill_search)
        
        # 技能表格
        left_layout.addWidget(self.skill_table)
        
        # 手焊单独显示
        hand_solder_box = QGroupBox("手焊技能评分 (单独计算，占比10%)", left_card)
        hand_solder_layout = QHBoxLayout(hand_solder_box)
        
        hand_solder_layout.addWidget(QLabel("手焊:"))
        self.hand_solder_spin = DoubleSpinBox(hand_solder_box)
        self.hand_solder_spin.setRange(0, 4)
        self.hand_solder_spin.setSingleStep(0.5)
        self.hand_solder_spin.setDecimals(1)
        hand_solder_layout.addWidget(self.hand_solder_spin)
        
        hand_solder_layout.addWidget(QLabel("满分4分"))
        hand_solder_layout.addStretch(1)
        
        left_layout.addWidget(hand_solder_box)
        
        content_splitter.addWidget(left_card)
        
        # 右侧: 其他技能评分和结果显示
        right_card = CardWidget(self)
        right_layout = QVBoxLayout(right_card)
        
        # 其他技能表单
        other_skills_box = QGroupBox("其他技能评分", right_card)
        skills_form = QFormLayout(other_skills_box)
        
        # 通用技能 (20%)
        self.general_skill_spin = DoubleSpinBox(other_skills_box)
        self.general_skill_spin.setRange(0, 100)
        self.general_skill_spin.setSingleStep(1)
        skills_form.addRow("通用技能 (20%):", self.general_skill_spin)
        
        # 跨部门技能 (10%)
        self.cross_dept_skill_spin = DoubleSpinBox(other_skills_box)
        self.cross_dept_skill_spin.setRange(0, 100)
        self.cross_dept_skill_spin.setSingleStep(1)
        skills_form.addRow("跨部门技能 (10%):", self.cross_dept_skill_spin)
        
        # 技师技能 (10%)
        self.technician_skill_spin = DoubleSpinBox(other_skills_box)
        self.technician_skill_spin.setRange(0, 100)
        self.technician_skill_spin.setSingleStep(1)
        skills_form.addRow("技师技能 (10%):", self.technician_skill_spin)
        
        # 管理技能 (10%)
        self.management_skill_spin = DoubleSpinBox(other_skills_box)
        self.management_skill_spin.setRange(0, 100)
        self.management_skill_spin.setSingleStep(1)
        skills_form.addRow("管理技能 (10%):", self.management_skill_spin)
        
        # 制度要求比例
        self.requirement_spin = DoubleSpinBox(other_skills_box)
        self.requirement_spin.setRange(0, 100)
        self.requirement_spin.setSingleStep(1)
        self.requirement_spin.setSuffix("%")
        skills_form.addRow("制度要求比例:", self.requirement_spin)
        
        right_layout.addWidget(other_skills_box)
        
        # 计算结果区域
        results_box = QGroupBox("计算结果", right_card)
        results_layout = QVBoxLayout(results_box)
        
        self.skill_score_label = QLabel("岗位技能得分: 0/204 (0%)", results_box)
        self.skill_score_label.setStyleSheet("font-weight: bold;")
        results_layout.addWidget(self.skill_score_label)
        
        self.hand_solder_label = QLabel("手焊技能得分: 0/4 (0%)", results_box)
        results_layout.addWidget(self.hand_solder_label)
        
        self.other_skills_label = QLabel("其他技能得分: 通用:0, 跨部门:0, 技师:0, 管理:0", results_box)
        results_layout.addWidget(self.other_skills_label)
        
        self.requirement_label = QLabel("制度要求比例: 0%", results_box)
        results_layout.addWidget(self.requirement_label)
        
        self.predicted_grade_label = QLabel("预测职级: 未评定", results_box)
        self.predicted_grade_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        results_layout.addWidget(self.predicted_grade_label)
        
        right_layout.addWidget(results_box)
        
        # 计算按钮
        calculate_layout = QHBoxLayout()
        
        self.calculate_btn = PrimaryPushButton("计算职级", right_card, FIF.CALCULATOR)
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
            WHERE department = 'AUT' AND category IN ('通用技能', '跨部门技能', '技师技能', '管理技能')
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
            return
            
        self.current_employee_no = emp_no
        self.load_scores()
        
    def load_scores(self):
        """加载员工成绩"""
        if not self.current_employee_no:
            return
            
        try:
            year = int(self.year_combo.currentText())
            
            # 清空所有得分
            self.clear_scores()
            
            # 获取员工所有成绩
            self.score_db.cursor.execute("""
            SELECT s.assessment_item_id, s.score, a.category
            FROM employee_scores s
            JOIN department_assessment_items a ON s.assessment_item_id = a.id
            WHERE s.employee_no = ? AND s.assessment_year = ?
            """, (self.current_employee_no, year))
            
            scores = self.score_db.cursor.fetchall()
            score_dict = {item_id: (score, category) for item_id, score, category in scores}
            
            # 填充岗位技能得分
            for row in range(self.skill_table.rowCount()):
                item_id = self.skill_table.item(row, 0).data(Qt.UserRole)
                if item_id in score_dict:
                    score_spin = self.skill_table.cellWidget(row, 2)
                    score_spin.setValue(score_dict[item_id][0])
            
            # 填充手焊得分
            if self.hand_solder_item and self.hand_solder_item[0] in score_dict:
                self.hand_solder_spin.setValue(score_dict[self.hand_solder_item[0]][0])
            
            # 填充其他技能得分
            for item_id, name, max_score, category in self.other_skills:
                if item_id in score_dict:
                    if category == '通用技能':
                        self.general_skill_spin.setValue(score_dict[item_id][0])
                    elif category == '跨部门技能':
                        self.cross_dept_skill_spin.setValue(score_dict[item_id][0])
                    elif category == '技师技能':
                        self.technician_skill_spin.setValue(score_dict[item_id][0])
                    elif category == '管理技能':
                        self.management_skill_spin.setValue(score_dict[item_id][0])
            
            # 获取预测职级和制度要求比例
            self.score_db.cursor.execute("""
            SELECT calculation_details FROM predicted_grades
            WHERE employee_no = ? AND assessment_year = ?
            """, (self.current_employee_no, year))
            
            result = self.score_db.cursor.fetchone()
            if result and result[0]:
                details = json.loads(result[0])
                if 'requirement_percent' in details:
                    self.requirement_spin.setValue(details['requirement_percent'])
            
            # 计算职级
            self.calculate_grade()
            
            print(f"成功加载员工 {self.current_employee_no} 在 {year} 年的成绩")
            
        except Exception as e:
            print(f"加载员工成绩失败: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_scores(self):
        """清空所有得分"""
        # 清空岗位技能得分
        for row in range(self.skill_table.rowCount()):
            score_spin = self.skill_table.cellWidget(row, 2)
            score_spin.setValue(0)
        
        # 清空手焊得分
        self.hand_solder_spin.setValue(0)
        
        # 清空其他技能得分
        self.general_skill_spin.setValue(0)
        self.cross_dept_skill_spin.setValue(0)
        self.technician_skill_spin.setValue(0)
        self.management_skill_spin.setValue(0)
        
        # 清空制度要求比例
        self.requirement_spin.setValue(0)
        
        # 重置计算结果
        self.skill_score_label.setText("岗位技能得分: 0/204 (0%)")
        self.hand_solder_label.setText("手焊技能得分: 0/4 (0%)")
        self.other_skills_label.setText("其他技能得分: 通用:0, 跨部门:0, 技师:0, 管理:0")
        self.requirement_label.setText("制度要求比例: 0%")
        self.predicted_grade_label.setText("预测职级: 未评定")
    
    def calculate_grade(self):
        """计算职级"""
        try:
            # 1. 计算岗位技能总分和百分比
            skill_total_score = 0
            skill_max_score = 204  # 固定值
            
            for row in range(self.skill_table.rowCount()):
                score_spin = self.skill_table.cellWidget(row, 2)
                skill_total_score += score_spin.value()
            
            skill_percent = (skill_total_score / skill_max_score) * 100
            
            # 2. 获取手焊得分和百分比
            hand_solder_score = self.hand_solder_spin.value()
            hand_solder_percent = (hand_solder_score / 4) * 100
            
            # 3. 获取其他技能得分
            general_skill = self.general_skill_spin.value()
            cross_dept_skill = self.cross_dept_skill_spin.value()
            technician_skill = self.technician_skill_spin.value()
            management_skill = self.management_skill_spin.value()
            
            # 4. 获取制度要求比例
            requirement_percent = self.requirement_spin.value()
            
            # 5. 更新结果显示
            self.skill_score_label.setText(f"岗位技能得分: {skill_total_score:.1f}/204 ({skill_percent:.1f}%)")
            self.hand_solder_label.setText(f"手焊技能得分: {hand_solder_score}/4 ({hand_solder_percent:.1f}%)")
            self.other_skills_label.setText(
                f"其他技能得分: 通用:{general_skill}, 跨部门:{cross_dept_skill}, 技师:{technician_skill}, 管理:{management_skill}"
            )
            self.requirement_label.setText(f"制度要求比例: {requirement_percent}%")
            
            # 6. 根据规则判断职级
            grade = self.determine_grade(skill_percent, requirement_percent)
            self.predicted_grade_label.setText(f"预测职级: {grade}")
            
            return {
                'skill_score': skill_total_score,
                'skill_percent': skill_percent,
                'hand_solder_score': hand_solder_score,
                'general_skill': general_skill,
                'cross_dept_skill': cross_dept_skill,
                'technician_skill': technician_skill,
                'management_skill': management_skill,
                'requirement_percent': requirement_percent,
                'predicted_grade': grade
            }
            
        except Exception as e:
            print(f"计算职级失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def determine_grade(self, skill_percent, requirement_percent):
        """根据岗位技能系数和制度要求比例判断职级"""
        # 按照表格判断职级
        if skill_percent >= 90 and 0 <= requirement_percent <= 5:
            return "J档 (优秀)"
        elif skill_percent >= 80 and 10 <= requirement_percent <= 20:
            return "J-档 (良好)"
        elif skill_percent >= 50 and 40 <= requirement_percent <= 50:
            return "合格档 (合格)"
        elif skill_percent >= 30 and 20 <= requirement_percent <= 40:
            return "不合格档 (不合格)"
        else:
            return "差档 (差)"
    
    def save_scores(self):
        """保存评分和计算结果"""
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
        
        try:
            year = int(self.year_combo.currentText())
            
            # 1. 保存岗位技能评分
            for row in range(self.skill_table.rowCount()):
                item_id = self.skill_table.item(row, 0).data(Qt.UserRole)
                score_spin = self.skill_table.cellWidget(row, 2)
                score_value = score_spin.value()
                
                self.save_score_item(item_id, score_value, year)
            
            # 2. 保存手焊评分
            if self.hand_solder_item:
                hand_solder_score = self.hand_solder_spin.value()
                self.save_score_item(self.hand_solder_item[0], hand_solder_score, year)
            
            # 3. 保存其他技能评分
            for item_id, name, max_score, category in self.other_skills:
                score_value = 0
                if category == '通用技能':
                    score_value = self.general_skill_spin.value()
                elif category == '跨部门技能':
                    score_value = self.cross_dept_skill_spin.value()
                elif category == '技师技能':
                    score_value = self.technician_skill_spin.value()
                elif category == '管理技能':
                    score_value = self.management_skill_spin.value()
                
                self.save_score_item(item_id, score_value, year)
            
            # 4. 计算并保存职级预测结果
            result = self.calculate_grade()
            if result:
                calculation_details = {
                    'skill_score': result['skill_score'],
                    'skill_percent': result['skill_percent'],
                    'hand_solder_score': result['hand_solder_score'],
                    'general_skill': result['general_skill'],
                    'cross_dept_skill': result['cross_dept_skill'],
                    'technician_skill': result['technician_skill'],
                    'management_skill': result['management_skill'],
                    'requirement_percent': result['requirement_percent'],
                    'predicted_grade': result['predicted_grade']
                }
                
                # 获取员工当前职级
                self.score_db.cursor.execute(
                    "SELECT grade_2024, grade_2023 FROM employees WHERE employee_no = ?", 
                    (self.current_employee_no,)
                )
                emp_result = self.score_db.cursor.fetchone()
                current_grade = emp_result[0] or emp_result[1] or "未设置"
                
                # 将结果保存到predicted_grades表
                self.score_db.cursor.execute("""
                INSERT OR REPLACE INTO predicted_grades
                (employee_no, assessment_year, current_grade, predicted_grade, 
                total_score, calculation_details)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_employee_no,
                    year,
                    current_grade,
                    result['predicted_grade'],
                    result['skill_score'],
                    json.dumps(calculation_details)
                ))
                self.score_db.conn.commit()
                
                InfoBar.success(
                    title='保存成功',
                    content=f"已保存员工 {self.employee_combo.currentText()} 的评分和预测结果",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            
        except Exception as e:
            print(f"保存评分失败: {e}")
            import traceback
            traceback.print_exc()
            
            InfoBar.error(
                title='保存失败',
                content=f"保存评分出错: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def save_score_item(self, item_id, score_value, year):
        """保存单个评分项目"""
        self.score_db.cursor.execute("""
        INSERT OR REPLACE INTO employee_scores
        (employee_no, assessment_year, assessment_item_id, score, created_by)
        VALUES (?, ?, ?, ?, ?)
        """, (
            self.current_employee_no,
            year,
            item_id,
            score_value,
            "系统"
        ))
        self.score_db.conn.commit()
    
    def refresh_scores(self):
        """刷新员工成绩"""
        if self.current_employee_no:
            self.load_scores()
"""

    # 修改主窗口类，添加新的视图
    main_window_update_code = """
# 在app/views/main_window.py中的MainWindow.__init__方法中添加
self.aut_score_view = AUTScoreView(self.score_db, self)

# 在app/views/main_window.py中的initNavigation方法中添加
self.navigationInterface.addItem(
    routeKey='aut_score',
    icon=FIF.EDIT,
    text='AUT成绩录入',
    position=NavigationItemPosition.TOP,
    onClick=lambda: self.switchTo(self.aut_score_view, 'aut_score')
)

# 在app/views/main_window.py中的initWindow方法中添加
self.addSubInterface(self.aut_score_view, 'aut_score', 'AUT成绩录入')
"""

    print("新的视图类代码已生成，您需要执行以下步骤：")
    print("\n1. 创建新文件：app/views/aut_score_view.py，将新视图类代码复制到此文件中")
    print("2. 修改app/views/main_window.py，添加新视图的引用和导航项")
    print("3. 运行程序测试新的AUT部门成绩录入界面")
    
    try:
        # 写入新视图类文件
        with open('app/views/aut_score_view.py', 'w', encoding='utf-8') as f:
            f.write(new_view_code)
        print("\n成功创建app/views/aut_score_view.py文件！")
        
        # 修改主窗口文件
        with open('app/views/main_window.py', 'r', encoding='utf-8') as f:
            main_window_code = f.read()
        
        # 添加导入语句
        if "from .aut_score_view import AUTScoreView" not in main_window_code:
            import_line = "from .employee_score_view import EmployeeScoreView"
            new_import = "from .employee_score_view import EmployeeScoreView\nfrom .aut_score_view import AUTScoreView"
            main_window_code = main_window_code.replace(import_line, new_import)
        
        # 添加视图实例
        if "self.aut_score_view = AUTScoreView" not in main_window_code:
            score_view_line = "self.employee_score_view = EmployeeScoreView(self.score_db, self)"
            new_line = score_view_line + "\n        self.aut_score_view = AUTScoreView(self.score_db, self)"
            main_window_code = main_window_code.replace(score_view_line, new_line)
        
        # 添加导航项
        if "routeKey='aut_score'" not in main_window_code:
            employee_score_nav = "            routeKey='employee_score',"
            employ_score_block = main_window_code.split(employee_score_nav)[1].split("self.navigationInterface.addItem")[0]
            
            # 找到下一个self.navigationInterface.addItem位置
            next_add = "self.navigationInterface.addItem"
            
            # 构建新的导航项
            new_nav_item = """
        self.navigationInterface.addItem(
            routeKey='aut_score',
            icon=FIF.EDIT,
            text='AUT成绩录入',
            position=NavigationItemPosition.TOP,
            onClick=lambda: self.switchTo(self.aut_score_view, 'aut_score')
        )
        """
            # 插入新导航项
            parts = main_window_code.split(next_add)
            main_window_code = parts[0] + new_nav_item + next_add + parts[1]
        
        # 添加子界面
        if "addSubInterface(self.aut_score_view" not in main_window_code:
            sub_interface_line = "self.addSubInterface(self.grade_analysis_view, 'grade_analysis', '职级预测分析')"
            new_sub = sub_interface_line + "\n        self.addSubInterface(self.aut_score_view, 'aut_score', 'AUT成绩录入')"
            main_window_code = main_window_code.replace(sub_interface_line, new_sub)
        
        # 写回修改后的代码
        with open('app/views/main_window.py', 'w', encoding='utf-8') as f:
            f.write(main_window_code)
        
        print("成功修改app/views/main_window.py文件！")
        print("\n所有修改已完成！请运行程序查看新的AUT部门成绩录入界面。")
        
    except Exception as e:
        print(f"创建或修改文件时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    redesign_score_view() 
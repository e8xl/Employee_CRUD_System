import os
import json
import datetime
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QFileDialog, QDialog, QGridLayout, QGroupBox
)
from qfluentwidgets import (
    PushButton, ComboBox, InfoBar, InfoBarPosition,
    FluentIcon as FIF, TableWidget, ScrollArea,
    TransparentToolButton, SimpleCardWidget, MessageBox
)

# 可选的matplotlib支持
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class GradeAnalysisView(QWidget):
    """职级预测分析视图"""
    
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
        self.department_combo.currentIndexChanged.connect(self.load_analysis_data)
        top_layout.addWidget(QLabel("部门:"))
        top_layout.addWidget(self.department_combo)
        
        # 添加年份选择下拉框
        self.year_combo = ComboBox(self)
        self.year_combo.setPlaceholderText("选择年份")
        
        # 添加年份选项
        current_year = datetime.datetime.now().year
        for year in range(current_year - 1, current_year + 5):
            self.year_combo.addItem(str(year), year)
        
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.setMinimumWidth(100)
        self.year_combo.currentIndexChanged.connect(self.load_analysis_data)
        top_layout.addWidget(QLabel("年份:"))
        top_layout.addWidget(self.year_combo)
        
        top_layout.addStretch(1)
        
        # 导出按钮
        self.export_button = PushButton("导出分析报告", self, FIF.SAVE)
        self.export_button.clicked.connect(self.export_report)
        top_layout.addWidget(self.export_button)
        
        main_layout.addLayout(top_layout)
        
        # 创建分析内容区域
        scroll_area = ScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        analysis_widget = QWidget(scroll_area)
        analysis_layout = QVBoxLayout(analysis_widget)
        
        # 统计摘要卡片
        self.summary_card = SimpleCardWidget(analysis_widget)
        summary_layout = QGridLayout(self.summary_card)
        
        # 添加统计摘要标签
        self.total_label = QLabel("总人数: 0", self.summary_card)
        self.total_label.setFont(QFont("Microsoft YaHei", 12))
        summary_layout.addWidget(self.total_label, 0, 0)
        
        self.promotion_label = QLabel("晋升人数: 0", self.summary_card)
        self.promotion_label.setFont(QFont("Microsoft YaHei", 12))
        summary_layout.addWidget(self.promotion_label, 0, 1)
        
        self.demotion_label = QLabel("降级人数: 0", self.summary_card)
        self.demotion_label.setFont(QFont("Microsoft YaHei", 12))
        summary_layout.addWidget(self.demotion_label, 0, 2)
        
        self.unchanged_label = QLabel("维持不变: 0", self.summary_card)
        self.unchanged_label.setFont(QFont("Microsoft YaHei", 12))
        summary_layout.addWidget(self.unchanged_label, 0, 3)
        
        analysis_layout.addWidget(self.summary_card)
        
        # 添加预测结果表格
        self.table_card = SimpleCardWidget(analysis_widget)
        table_layout = QVBoxLayout(self.table_card)
        
        self.result_table = TableWidget(self.table_card)
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels(['员工工号', '员工姓名', '当前职级', '预测职级', '总分', '详情'])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        table_layout.addWidget(self.result_table)
        analysis_layout.addWidget(self.table_card)
        
        scroll_area.setWidget(analysis_widget)
        main_layout.addWidget(scroll_area)
    
    def load_departments(self):
        """加载部门列表"""
        departments = self.score_db.get_all_departments()
        for dept in departments:
            self.department_combo.addItem(dept, dept)
    
    def load_analysis_data(self):
        """加载分析数据"""
        department = self.department_combo.currentData()
        year = self.year_combo.currentData()
        
        if not department or not year:
            return
        
        # 获取部门预测职级结果
        predicted_grades = self.score_db.get_department_predicted_grades(department, year)
        
        # 更新统计摘要
        self.update_statistics(predicted_grades)
        
        # 更新表格
        self.update_table(predicted_grades)
    
    def update_statistics(self, predicted_grades):
        """更新统计摘要"""
        total_count = len(predicted_grades)
        promotion_count = 0
        demotion_count = 0
        unchanged_count = 0
        
        for grade_data in predicted_grades:
            current_grade = grade_data['current_grade']
            predicted_grade = grade_data['predicted_grade']
            
            if current_grade == predicted_grade:
                unchanged_count += 1
            elif self._is_promotion(current_grade, predicted_grade):
                promotion_count += 1
            else:
                demotion_count += 1
        
        # 更新标签
        self.total_label.setText(f"总人数: {total_count}")
        self.promotion_label.setText(f"晋升人数: {promotion_count}")
        self.demotion_label.setText(f"降级人数: {demotion_count}")
        self.unchanged_label.setText(f"维持不变: {unchanged_count}")
    
    def update_table(self, predicted_grades):
        """更新表格"""
        self.result_table.setRowCount(0)
        
        for row, grade_data in enumerate(predicted_grades):
            self.result_table.insertRow(row)
            
            # 员工工号
            no_item = QTableWidgetItem(grade_data['employee_no'])
            self.result_table.setItem(row, 0, no_item)
            
            # 员工姓名
            name_item = QTableWidgetItem(grade_data['employee_name'])
            self.result_table.setItem(row, 1, name_item)
            
            # 当前职级
            current_grade_item = QTableWidgetItem(grade_data['current_grade'])
            self.result_table.setItem(row, 2, current_grade_item)
            
            # 预测职级
            predicted_grade_item = QTableWidgetItem(grade_data['predicted_grade'])
            
            # 根据晋升/降级/不变设置不同的背景色
            if grade_data['current_grade'] == grade_data['predicted_grade']:
                # 不变 - 白色
                pass
            elif self._is_promotion(grade_data['current_grade'], grade_data['predicted_grade']):
                # 晋升 - 绿色
                predicted_grade_item.setBackground(QColor(200, 255, 200))
            else:
                # 降级 - 红色
                predicted_grade_item.setBackground(QColor(255, 200, 200))
            
            self.result_table.setItem(row, 3, predicted_grade_item)
            
            # 总分
            score_item = QTableWidgetItem(str(grade_data['total_score']))
            self.result_table.setItem(row, 4, score_item)
            
            # 详情按钮
            details_layout = QHBoxLayout()
            details_layout.setContentsMargins(4, 4, 4, 4)
            
            details_button = TransparentToolButton(FIF.INFO)
            details_button.setFixedSize(QSize(30, 30))
            details_button.setToolTip("查看详细信息")
            details_button.clicked.connect(lambda _, data=grade_data: self.show_details(data))
            
            details_layout.addWidget(details_button)
            details_layout.addStretch(1)
            
            details_widget = QWidget()
            details_widget.setLayout(details_layout)
            
            self.result_table.setCellWidget(row, 5, details_widget)
    
    def show_details(self, grade_data):
        """显示详细信息"""
        dialog = GradeDetailsDialog(self, grade_data)
        dialog.exec_()
    
    def export_report(self):
        """导出分析报告"""
        department = self.department_combo.currentData()
        year = self.year_combo.currentData()
        
        if not department or not year:
            InfoBar.error(
                title='导出失败',
                content="请先选择部门和年份",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存分析报告", f"{department}部门_{year}年_职级预测分析报告", "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        try:
            # 获取部门预测职级结果
            predicted_grades = self.score_db.get_department_predicted_grades(department, year)
            
            # 使用pandas导出到Excel
            import pandas as pd
            
            # 准备预测职级表格数据
            predicted_data = []
            
            for grade_data in predicted_grades:
                current_grade = grade_data['current_grade']
                predicted_grade = grade_data['predicted_grade']
                
                # 确定变化类型
                if current_grade == predicted_grade:
                    change_type = "维持不变"
                elif self._is_promotion(current_grade, predicted_grade):
                    change_type = "晋升"
                else:
                    change_type = "降级"
                
                # 添加到表格数据
                predicted_data.append({
                    '员工工号': grade_data['employee_no'],
                    '员工姓名': grade_data['employee_name'],
                    '当前职级': current_grade,
                    '预测职级': predicted_grade,
                    '总分': grade_data['total_score'],
                    '变化类型': change_type
                })
            
            # 创建DataFrame并导出
            df = pd.DataFrame(predicted_data)
            df.to_excel(file_path, index=False)
            
            InfoBar.success(
                title='导出成功',
                content=f"已成功导出分析报告到 {file_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            InfoBar.error(
                title='导出失败',
                content=f"导出分析报告时出现错误: {str(e)}",
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


class GradeDetailsDialog(QDialog):
    """职级预测详细信息对话框"""
    
    def __init__(self, parent=None, grade_data=None):
        super().__init__(parent)
        self.grade_data = grade_data
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("职级预测详细信息")
        self.setMinimumSize(600, 400)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 员工信息区域
        info_group = QGroupBox("员工信息", self)
        info_layout = QGridLayout(info_group)
        
        # 员工姓名和工号
        info_layout.addWidget(QLabel("姓名:"), 0, 0)
        info_layout.addWidget(QLabel(self.grade_data['employee_name']), 0, 1)
        
        info_layout.addWidget(QLabel("工号:"), 0, 2)
        info_layout.addWidget(QLabel(self.grade_data['employee_no']), 0, 3)
        
        # 部门
        info_layout.addWidget(QLabel("部门:"), 1, 0)
        info_layout.addWidget(QLabel(self.grade_data['department']), 1, 1)
        
        # 职级变化
        info_layout.addWidget(QLabel("当前职级:"), 1, 2)
        info_layout.addWidget(QLabel(self.grade_data['current_grade']), 1, 3)
        
        info_layout.addWidget(QLabel("预测职级:"), 2, 0)
        predicted_grade_label = QLabel(self.grade_data['predicted_grade'])
        
        # 根据晋升/降级/不变设置不同的颜色
        if self.grade_data['current_grade'] == self.grade_data['predicted_grade']:
            # 不变 - 黑色
            pass
        elif self._is_promotion(self.grade_data['current_grade'], self.grade_data['predicted_grade']):
            # 晋升 - 绿色
            predicted_grade_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            # 降级 - 红色
            predicted_grade_label.setStyleSheet("color: red; font-weight: bold;")
            
        info_layout.addWidget(predicted_grade_label, 2, 1)
        
        info_layout.addWidget(QLabel("总分:"), 2, 2)
        info_layout.addWidget(QLabel(str(self.grade_data['total_score'])), 2, 3)
        
        layout.addWidget(info_group)
        
        # 分数详情区域
        scores_group = QGroupBox("成绩详情", self)
        scores_layout = QVBoxLayout(scores_group)
        
        # 创建表格
        self.scores_table = TableWidget(scores_group)
        self.scores_table.setColumnCount(4)
        self.scores_table.setHorizontalHeaderLabels(['考核项目', '权重', '得分', '加权得分'])
        self.scores_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        scores_layout.addWidget(self.scores_table)
        
        layout.addWidget(scores_group)
        
        # 填充成绩详情
        self.fill_scores()
        
        # 添加关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        close_button = PushButton("关闭", self)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def fill_scores(self):
        """填充成绩详情"""
        if 'calculation_details' not in self.grade_data:
            return
            
        calculation_details = self.grade_data['calculation_details']
        
        if 'scores' not in calculation_details:
            return
            
        scores = calculation_details['scores']
        
        # 填充表格
        self.scores_table.setRowCount(len(scores))
        
        for row, score in enumerate(scores):
            # 考核项目
            self.scores_table.setItem(row, 0, QTableWidgetItem(score['item']))
            
            # 权重
            self.scores_table.setItem(row, 1, QTableWidgetItem(str(score['weight'])))
            
            # 得分
            self.scores_table.setItem(row, 2, QTableWidgetItem(str(score['raw_score'])))
            
            # 加权得分
            self.scores_table.setItem(row, 3, QTableWidgetItem(str(score['weighted_score'])))
    
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
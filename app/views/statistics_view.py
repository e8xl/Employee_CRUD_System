from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QScrollArea, QSplitter, QFrame
)
from PyQt5.QtGui import QFont
from qfluentwidgets import (
    ComboBox, PushButton, CardWidget, FluentIcon, 
    InfoBar, InfoBarPosition, ToolButton, ScrollArea
)
from app.utils.chart_generator import ChartGenerator, MatplotlibCanvas
import matplotlib.pyplot as plt

class StatisticsView(QWidget):
    """统计视图，用于显示员工统计数据和图表"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent = parent
        
        # 图表相关
        self.chart_generator = ChartGenerator()
        self.current_chart = None
        
        # 初始化UI
        self.initUI()
        
        # 加载统计数据
        self.loadStatistics()
        
    def initUI(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # 顶部工具栏
        top_bar = QHBoxLayout()
        
        # 标题
        title_label = QLabel("统计分析")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        # 图表类型选择
        self.chart_type_combo = ComboBox(self)
        self.chart_type_combo.addItems([
            "职级分布", "部门分布", "职级趋势", "晋升分析"
        ])
        self.chart_type_combo.setCurrentIndex(0)
        self.chart_type_combo.currentIndexChanged.connect(self.onChartTypeChanged)
        top_bar.addWidget(QLabel("图表类型:"))
        top_bar.addWidget(self.chart_type_combo)
        
        # 年份选择（针对职级分布和晋升分析）
        self.year_combo = ComboBox(self)
        self.year_combo.addItems(["2020", "2021", "2022", "2023", "2024", "2025"])
        self.year_combo.setCurrentText("2024")  # 默认选择当前年份
        self.year_combo.currentTextChanged.connect(self.updateChart)
        top_bar.addWidget(QLabel("年份:"))
        top_bar.addWidget(self.year_combo)
        
        # 刷新按钮
        self.refresh_btn = PushButton('刷新数据', self)
        self.refresh_btn.setIcon(FluentIcon.SYNC)
        self.refresh_btn.clicked.connect(self.loadStatistics)
        top_bar.addWidget(self.refresh_btn)
        
        main_layout.addLayout(top_bar)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        
        # 左侧：图表区域
        self.chart_widget = QWidget()
        chart_layout = QVBoxLayout(self.chart_widget)
        chart_layout.setContentsMargins(15, 15, 15, 15)
        
        # 图表容器
        self.chart_card = CardWidget(self)
        self.chart_container = QVBoxLayout(self.chart_card)
        self.chart_container.setContentsMargins(20, 20, 20, 20)
        
        # 初始化图表
        self.chart_canvas = MatplotlibCanvas(self)
        self.chart_container.addWidget(self.chart_canvas)
        chart_layout.addWidget(self.chart_card)
        
        # 右侧：数据面板
        self.data_widget = QWidget()
        data_layout = QVBoxLayout(self.data_widget)
        data_layout.setContentsMargins(0, 0, 0, 0)
        
        # 数据卡片
        self.data_card = CardWidget(self)
        self.data_card.setMinimumWidth(300)
        self.data_card.setMaximumWidth(400)
        data_card_layout = QVBoxLayout(self.data_card)
        data_card_layout.setContentsMargins(15, 15, 15, 15)
        
        # 数据标题
        data_title = QLabel("数据摘要")
        data_title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        data_card_layout.addWidget(data_title)
        
        # 数据内容区域（使用滚动区域）
        self.data_scroll = ScrollArea(self.data_card)
        self.data_scroll.setWidgetResizable(True)
        
        # 数据内容容器
        self.data_content = QWidget()
        self.data_content_layout = QVBoxLayout(self.data_content)
        self.data_content_layout.setContentsMargins(5, 5, 5, 5)
        self.data_content_layout.setSpacing(10)
        self.data_content_layout.addStretch()
        
        self.data_scroll.setWidget(self.data_content)
        data_card_layout.addWidget(self.data_scroll)
        
        data_layout.addWidget(self.data_card)
        
        # 添加到分割器
        splitter.addWidget(self.chart_widget)
        splitter.addWidget(self.data_widget)
        
        # 设置分割比例
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter)
        
        # 设置布局
        self.setLayout(main_layout)
    
    def loadStatistics(self):
        """加载统计数据"""
        try:
            # 获取当前选中的图表类型
            chart_type = self.chart_type_combo.currentText()
            
            # 刷新图表
            self.updateChart()
            
            # 显示成功提示
            InfoBar.success(
                title='数据加载成功',
                content=f"已成功加载{chart_type}数据",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        except Exception as e:
            # 显示错误提示
            InfoBar.error(
                title='数据加载失败',
                content=f"加载统计数据时发生错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def onChartTypeChanged(self, index):
        """图表类型改变时的处理函数"""
        # 获取当前所选图表类型
        chart_type = self.chart_type_combo.currentText()
        
        # 根据图表类型启用或禁用年份选择
        year_required = chart_type in ["职级分布", "晋升分析"]
        self.year_combo.setEnabled(year_required)
        
        # 更新图表
        self.updateChart()
    
    def updateChart(self):
        """更新图表"""
        try:
            # 清除数据面板中的旧数据
            self.clearDataPanel()
            
            # 获取当前选中的图表类型和年份
            chart_type = self.chart_type_combo.currentText()
            year = self.year_combo.currentText() if self.year_combo.isEnabled() else None
            
            # 清除旧图表
            self.chart_canvas.figure.clear()
            
            # 创建新图表
            ax = self.chart_canvas.figure.add_subplot(111)
            
            # 根据图表类型生成不同的图表
            if chart_type == "职级分布":
                self.generateGradeDistribution(ax, year)
            elif chart_type == "部门分布":
                self.generateDepartmentDistribution(ax)
            elif chart_type == "职级趋势":
                self.generateGradeTrend(ax)
            elif chart_type == "晋升分析":
                self.generatePromotionAnalysis(ax, year)
            
            # 刷新图表
            self.chart_canvas.draw()
            
        except Exception as e:
            print(f"更新图表时发生错误: {str(e)}")
            InfoBar.error(
                title='图表更新失败',
                content=f"更新图表时发生错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def clearDataPanel(self):
        """清除数据面板中的数据项"""
        # 清除数据内容布局中的所有控件
        while self.data_content_layout.count() > 1:  # 保留最后一个stretch
            item = self.data_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def addDataItem(self, label, value):
        """向数据面板添加数据项"""
        # 创建数据项容器
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Microsoft YaHei", 10))
        item_layout.addWidget(label_widget)
        
        item_layout.addStretch()
        
        # 值
        value_widget = QLabel(str(value))
        value_widget.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        item_layout.addWidget(value_widget)
        
        # 添加到数据面板
        self.data_content_layout.insertWidget(self.data_content_layout.count() - 1, item_widget)
    
    def generateGradeDistribution(self, ax, year):
        """生成职级分布图表"""
        # 获取数据
        employees = self.db.get_all_employees()
        
        # 按职级统计人数
        grade_counts = {}
        for emp in employees:
            grade = emp.get(f'grade_{year}', '')
            if grade:
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # 定义职级顺序
        grade_order = {'G1': 1, 'G2': 2, 'G3': 3, 'G4B': 4, 'G4A': 5, 'Technian': 6}
        
        # 准备绘图数据，按照职级顺序排序
        ordered_grades = []
        ordered_counts = []
        
        # 按顺序添加数据
        for grade in sorted(grade_counts.keys(), key=lambda g: grade_order.get(g, 0)):
            ordered_grades.append(grade)
            ordered_counts.append(grade_counts[grade])
        
        # 绘制条形图
        bars = ax.bar(ordered_grades, ordered_counts)
        
        # 设置图表标题和标签
        ax.set_title(f'{year}年职级分布')
        ax.set_xlabel('职级')
        ax.set_ylabel('人数')
        
        # 在条形上方显示数值
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    '%d' % int(height),
                    ha='center', va='bottom')
        
        # 设置网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 添加数据到数据面板
        self.addDataItem("总人数", sum(ordered_counts))
        for grade, count in zip(ordered_grades, ordered_counts):
            self.addDataItem(f"{grade}", count)
    
    def generateDepartmentDistribution(self, ax):
        """生成部门分布图表"""
        # 获取数据
        employees = self.db.get_all_employees()
        
        # 按部门统计人数
        dept_counts = {}
        for emp in employees:
            dept = emp.get('department', '')
            if dept:
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        # 准备绘图数据
        departments = list(dept_counts.keys())
        counts = list(dept_counts.values())
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(counts, autopct='%1.1f%%', startangle=90)
        
        # 设置图表标题
        ax.set_title('部门人员分布')
        
        # 添加图例
        ax.legend(wedges, departments, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        # 确保饼图是圆形的
        ax.axis('equal')
        
        # 添加数据到数据面板
        self.addDataItem("总人数", sum(counts))
        for dept, count in zip(departments, counts):
            self.addDataItem(f"{dept}", count)
    
    def generateGradeTrend(self, ax):
        """生成职级趋势图表"""
        # 获取数据
        employees = self.db.get_all_employees()
        
        # 年份列表
        years = ["2020", "2021", "2022", "2023", "2024"]
        
        # 获取所有职级
        all_grades = set()
        for emp in employees:
            for year in years:
                grade = emp.get(f'grade_{year}', '')
                if grade:
                    all_grades.add(grade)
        
        # 定义职级顺序
        grade_order = {'G1': 1, 'G2': 2, 'G3': 3, 'G4B': 4, 'G4A': 5, 'Technian': 6}
        
        # 按顺序排列职级
        all_grades = sorted(list(all_grades), key=lambda g: grade_order.get(g, 0))
        
        # 统计每年每个职级的人数
        grade_counts = {grade: [] for grade in all_grades}
        
        for year in years:
            year_counts = {grade: 0 for grade in all_grades}
            
            for emp in employees:
                grade = emp.get(f'grade_{year}', '')
                if grade in all_grades:
                    year_counts[grade] += 1
            
            for grade in all_grades:
                grade_counts[grade].append(year_counts[grade])
        
        # 绘制线图
        for grade, counts in grade_counts.items():
            ax.plot(years, counts, marker='o', label=grade)
        
        # 设置图表标题和标签
        ax.set_title('职级分布趋势')
        ax.set_xlabel('年份')
        ax.set_ylabel('人数')
        
        # 添加图例
        ax.legend()
        
        # 设置网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 添加数据到数据面板
        for year_index, year in enumerate(years):
            total = sum(counts[year_index] for counts in grade_counts.values())
            self.addDataItem(f"{year}年总人数", total)
            
        for grade, counts in grade_counts.items():
            self.addDataItem(f"{grade}(当前)", counts[-1])
    
    def generatePromotionAnalysis(self, ax, year):
        """生成晋升分析图表"""
        # 获取数据
        employees = self.db.get_all_employees()
        
        # 查找前一年
        prev_year = str(int(year) - 1)
        
        # 定义职级顺序
        grade_order = {'G1': 1, 'G2': 2, 'G3': 3, 'G4B': 4, 'G4A': 5, 'Technian': 6}
        
        # 统计晋升情况
        promotion_data = {'晋升': 0, '平级': 0, '降级': 0, '新入职': 0}
        
        for emp in employees:
            curr_grade = emp.get(f'grade_{year}', '')
            prev_grade = emp.get(f'grade_{prev_year}', '')
            
            if not curr_grade:
                continue
            
            if not prev_grade:
                promotion_data['新入职'] += 1
            else:
                # 根据职级顺序判断晋升情况
                curr_level = grade_order.get(curr_grade, 0)
                prev_level = grade_order.get(prev_grade, 0)
                
                if curr_level > prev_level:
                    promotion_data['晋升'] += 1
                elif curr_level < prev_level:
                    promotion_data['降级'] += 1
                else:
                    promotion_data['平级'] += 1
        
        # 准备绘图数据
        categories = list(promotion_data.keys())
        counts = list(promotion_data.values())
        
        # 绘制条形图
        bars = ax.bar(categories, counts, color=['green', 'blue', 'red', 'gray'])
        
        # 设置图表标题和标签
        ax.set_title(f'{prev_year}至{year}年晋升分析')
        ax.set_xlabel('变化类型')
        ax.set_ylabel('人数')
        
        # 在条形上方显示数值
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    '%d' % int(height),
                    ha='center', va='bottom')
        
        # 设置网格线
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 添加数据到数据面板
        total = sum(counts)
        self.addDataItem("总计", total)
        
        for category, count in zip(categories, counts):
            percentage = 0 if total == 0 else round(count / total * 100, 1)
            self.addDataItem(f"{category}", f"{count} ({percentage}%)") 
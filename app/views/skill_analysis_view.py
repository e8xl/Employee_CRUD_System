from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGridLayout, QSizePolicy
)
from qfluentwidgets import (
    PushButton, ComboBox, InfoBar, InfoBarPosition, 
    CardWidget, FluentIcon
)
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import datetime

# 自定义统计卡片组件，替代StatsCard
class StatCard(CardWidget):
    """自定义统计卡片组件"""
    def __init__(self, title, value, prefix="", suffix="", icon=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.value_text = value
        self.prefix = prefix
        self.suffix = suffix
        self.icon = icon
        
        # 设置卡片尺寸
        self.setFixedHeight(120)
        
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 如果有图标，添加图标
        if icon:
            icon_label = QLabel(self)
            icon_label.setFixedSize(32, 32)
            icon_label.setPixmap(icon.icon(theme='light').pixmap(32, 32))
            layout.addWidget(icon_label)
            layout.addSpacing(10)
        
        # 添加文本信息
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        title_label = QLabel(title, self)
        title_label.setStyleSheet("font-size: 14px; color: gray;")
        text_layout.addWidget(title_label)
        
        value_layout = QHBoxLayout()
        value_layout.setSpacing(2)
        
        if prefix:
            prefix_label = QLabel(prefix, self)
            prefix_label.setStyleSheet("font-size: 16px;")
            value_layout.addWidget(prefix_label)
        
        self.value_label = QLabel(value, self)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        value_layout.addWidget(self.value_label)
        
        if suffix:
            suffix_label = QLabel(suffix, self)
            suffix_label.setStyleSheet("font-size: 16px;")
            value_layout.addWidget(suffix_label)
        
        value_layout.addStretch(1)
        text_layout.addLayout(value_layout)
        
        layout.addLayout(text_layout)
        layout.addStretch(1)
    
    def setValue(self, value):
        """更新值"""
        self.value_text = value
        self.value_label.setText(value)

class MatplotlibCanvas(FigureCanvas):
    """Matplotlib画布"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use('ggplot')  # 使用ggplot样式
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class SkillAnalysisView(QWidget):
    """技能分析视图，用于显示技能评分的统计和分析"""
    
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
        
        # 统计卡片区域
        self.createStatsCards(layout)
        
        # 图表区域
        self.createCharts(layout)
        
        # 加载初始数据
        self.current_year = datetime.datetime.now().year
        self.year_combo.setCurrentText(str(self.current_year))
        self.loadData()
        
    def createControlPanel(self, parent_layout):
        """创建控制面板"""
        control_card = CardWidget(self)
        control_layout = QHBoxLayout(control_card)
        control_layout.setContentsMargins(20, 20, 20, 20)
        
        # 年份选择
        year_label = QLabel("选择年份:", self)
        control_layout.addWidget(year_label)
        
        self.year_combo = ComboBox(self)
        years = [str(y) for y in range(2020, datetime.datetime.now().year + 2)]
        self.year_combo.addItems(years)
        self.year_combo.setCurrentText(str(datetime.datetime.now().year))
        self.year_combo.currentTextChanged.connect(self.yearChanged)
        control_layout.addWidget(self.year_combo)
        
        control_layout.addStretch(1)
        
        # 刷新按钮
        self.refresh_btn = PushButton("刷新数据", self)
        self.refresh_btn.setIcon(FluentIcon.SYNC)
        self.refresh_btn.clicked.connect(self.loadData)
        control_layout.addWidget(self.refresh_btn)
        
        parent_layout.addWidget(control_card)
        
    def createStatsCards(self, parent_layout):
        """创建统计卡片区域"""
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        # 总人数卡片
        self.total_employees_card = StatCard(
            title="总人数",
            value="0",
            prefix="",
            suffix="人",
            icon=FluentIcon.PEOPLE
        )
        stats_layout.addWidget(self.total_employees_card, 0, 0)
        
        # 各职级人数卡片
        self.g1_card = StatCard(
            title="G1职级",
            value="0",
            prefix="",
            suffix="人",
            icon=FluentIcon.PEOPLE
        )
        stats_layout.addWidget(self.g1_card, 0, 1)
        
        self.g2_card = StatCard(
            title="G2职级",
            value="0",
            prefix="",
            suffix="人",
            icon=FluentIcon.PEOPLE
        )
        stats_layout.addWidget(self.g2_card, 0, 2)
        
        self.g3_card = StatCard(
            title="G3职级",
            value="0",
            prefix="",
            suffix="人",
            icon=FluentIcon.PEOPLE
        )
        stats_layout.addWidget(self.g3_card, 1, 0)
        
        self.g4a_card = StatCard(
            title="G4A职级",
            value="0",
            prefix="",
            suffix="人",
            icon=FluentIcon.PEOPLE
        )
        stats_layout.addWidget(self.g4a_card, 1, 1)
        
        self.g4b_card = StatCard(
            title="G4B职级",
            value="0",
            prefix="",
            suffix="人",
            icon=FluentIcon.PEOPLE
        )
        stats_layout.addWidget(self.g4b_card, 1, 2)
        
        parent_layout.addLayout(stats_layout)
        
    def createCharts(self, parent_layout):
        """创建图表区域"""
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)
        
        # 职级分布饼图
        grade_card = CardWidget(self)
        grade_layout = QVBoxLayout(grade_card)
        grade_layout.setContentsMargins(15, 15, 15, 15)
        
        grade_title = QLabel("职级分布", self)
        grade_title.setAlignment(Qt.AlignCenter)
        grade_layout.addWidget(grade_title)
        
        self.grade_canvas = MatplotlibCanvas(self, width=4, height=4)
        grade_layout.addWidget(self.grade_canvas)
        
        charts_layout.addWidget(grade_card)
        
        # 技能分数分布图
        skill_card = CardWidget(self)
        skill_layout = QVBoxLayout(skill_card)
        skill_layout.setContentsMargins(15, 15, 15, 15)
        
        skill_title = QLabel("技能分数分布", self)
        skill_title.setAlignment(Qt.AlignCenter)
        skill_layout.addWidget(skill_title)
        
        self.skill_canvas = MatplotlibCanvas(self, width=5, height=4)
        skill_layout.addWidget(self.skill_canvas)
        
        charts_layout.addWidget(skill_card)
        
        parent_layout.addLayout(charts_layout)
        
    def yearChanged(self, year):
        """年份变化时重新加载数据"""
        self.current_year = int(year)
        self.loadData()
        
    def loadData(self):
        """加载数据并更新视图"""
        try:
            # 获取技能统计数据
            stats = self.db.get_skill_statistics(self.current_year)
            
            # 更新统计卡片
            grade_distribution = stats.get('grade_distribution', {})
            total = sum(grade_distribution.values())
            
            self.total_employees_card.setValue(str(total))
            self.g1_card.setValue(str(grade_distribution.get('G1', 0)))
            self.g2_card.setValue(str(grade_distribution.get('G2', 0)))
            self.g3_card.setValue(str(grade_distribution.get('G3', 0)))
            self.g4a_card.setValue(str(grade_distribution.get('G4A', 0)))
            self.g4b_card.setValue(str(grade_distribution.get('G4B', 0)))
            
            # 更新职级分布饼图
            self.updateGradeChart(grade_distribution)
            
            # 更新技能分数分布图
            skill_distributions = stats.get('skill_distributions', {})
            self.updateSkillChart(skill_distributions)
        
        except Exception as e:
            print(f"加载技能分析数据失败: {e}")
            InfoBar.error(
                title='加载失败',
                content=f"加载技能分析数据失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def updateGradeChart(self, grade_distribution):
        """更新职级分布饼图"""
        try:
            # 清除旧图
            self.grade_canvas.axes.clear()
            
            # 如果没有数据，显示空饼图
            if not grade_distribution or sum(grade_distribution.values()) == 0:
                self.grade_canvas.axes.text(0.5, 0.5, "无数据", 
                               horizontalalignment='center',
                               verticalalignment='center',
                               transform=self.grade_canvas.axes.transAxes,
                               fontsize=12)
                self.grade_canvas.draw()
                return
            
            # 提取职级和人数
            grades = list(grade_distribution.keys())
            counts = list(grade_distribution.values())
            
            # 绘制饼图
            self.grade_canvas.axes.pie(
                counts, 
                labels=grades, 
                autopct='%1.1f%%',
                startangle=90,
                colors=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC']
            )
            self.grade_canvas.axes.axis('equal')  # 确保饼图是圆的
            
            # 添加标题
            self.grade_canvas.axes.set_title(f"{self.current_year}年职级分布")
            
            self.grade_canvas.draw()
        
        except Exception as e:
            print(f"更新职级分布图表失败: {e}")
    
    def updateSkillChart(self, skill_distributions):
        """更新技能分数分布图"""
        try:
            # 清除旧图
            self.skill_canvas.axes.clear()
            
            # 如果没有数据，显示空图
            if not skill_distributions:
                self.skill_canvas.axes.text(0.5, 0.5, "无数据", 
                               horizontalalignment='center',
                               verticalalignment='center',
                               transform=self.skill_canvas.axes.transAxes,
                               fontsize=12)
                self.skill_canvas.draw()
                return
            
            # 准备数据
            skill_types = list(skill_distributions.keys())
            x = range(len(skill_types))
            
            # 设置柱状图宽度和位置
            width = 0.15
            score_ranges = ['0-20', '20-40', '40-60', '60-80', '80-100']
            colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC']
            
            # 绘制柱状图
            for i, score_range in enumerate(score_ranges):
                heights = [skill_distributions[skill].get(score_range, 0) for skill in skill_types]
                self.skill_canvas.axes.bar(
                    [p + width * i for p in x], 
                    heights, 
                    width, 
                    label=score_range,
                    color=colors[i]
                )
            
            # 设置坐标轴和标签
            self.skill_canvas.axes.set_ylabel('人数')
            self.skill_canvas.axes.set_title(f"{self.current_year}年技能分数分布")
            self.skill_canvas.axes.set_xticks([p + width * 2 for p in x])
            self.skill_canvas.axes.set_xticklabels(skill_types)
            
            # 添加图例
            self.skill_canvas.axes.legend(loc='upper right')
            
            # 调整布局
            self.skill_canvas.fig.tight_layout()
            
            self.skill_canvas.draw()
        
        except Exception as e:
            print(f"更新技能分数分布图表失败: {e}")
            self.skill_canvas.axes.text(0.5, 0.5, f"图表更新失败: {str(e)}", 
                           horizontalalignment='center',
                           verticalalignment='center',
                           transform=self.skill_canvas.axes.transAxes,
                           fontsize=10)
            self.skill_canvas.draw() 
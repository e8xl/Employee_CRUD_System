import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class ChartGenerator:
    """生成各种图表的工具类"""
    
    @staticmethod
    def create_grade_distribution_chart(stats, year=None):
        """创建职级分布图表"""
        grade_distribution = stats.get('grade_distribution', {})
        
        if not year:
            # 获取最新的一年
            years = list(grade_distribution.keys())
            if not years:
                return None
            years.sort()
            year = years[-1]
        
        data = grade_distribution.get(year, {})
        if not data:
            return None
        
        # 提取数据
        grades = list(data.keys())
        counts = list(data.values())
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(grades, counts, color='skyblue')
        
        # 在柱状图上添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.0f}',
                    ha='center', va='bottom')
        
        ax.set_title(f'{year[6:]} 年职级分布')
        ax.set_xlabel('职级')
        ax.set_ylabel('人数')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        return fig
    
    @staticmethod
    def create_department_distribution_chart(stats):
        """创建部门分布图表"""
        department_distribution = stats.get('department_distribution', {})
        if not department_distribution:
            return None
        
        # 提取数据
        departments = list(department_distribution.keys())
        counts = list(department_distribution.values())
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 8))
        # 如果部门太多，使用水平条形图
        if len(departments) > 10:
            # 排序
            sorted_data = sorted(zip(departments, counts), key=lambda x: x[1], reverse=True)
            departments, counts = zip(*sorted_data)
            
            bars = ax.barh(departments, counts, color='lightgreen')
            
            # 在条形图上添加数值标签
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                        f'{width:.0f}',
                        ha='left', va='center')
            
            ax.set_title('各部门人员分布')
            ax.set_xlabel('人数')
            ax.set_ylabel('部门')
            ax.grid(axis='x', linestyle='--', alpha=0.7)
        else:
            # 使用饼图
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.pie(counts, labels=departments, autopct='%1.1f%%', 
                   shadow=False, startangle=90)
            ax.axis('equal')  # 使饼图为正圆形
            ax.set_title('各部门人员分布')
        
        return fig
    
    @staticmethod
    def create_grade_trend_chart(all_employees):
        """创建职级趋势图表"""
        if not all_employees:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(all_employees)
        
        # 准备数据
        years = ['2020', '2021', '2022', '2023', '2024', '2025']
        grade_columns = [f'grade_{year}' for year in years]
        
        # 初始化数据结构
        trend_data = {grade: [] for grade in ['G1', 'G2', 'G3', 'G4A', 'G4B', 'Technian']}
        
        # 统计每年各职级的人数
        for col in grade_columns:
            grade_counts = df[col].value_counts().to_dict()
            for grade, count in trend_data.items():
                count.append(grade_counts.get(grade, 0))
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 为每个职级绘制折线
        for grade, counts in trend_data.items():
            if sum(counts) > 0:  # 只绘制有数据的职级
                ax.plot(years, counts, marker='o', linewidth=2, label=grade)
        
        ax.set_title('职级变化趋势')
        ax.set_xlabel('年份')
        ax.set_ylabel('人数')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        return fig
    
    @staticmethod
    def create_promotion_analysis_chart(all_employees, base_year='2023', target_year='2024'):
        """创建晋升分析图表"""
        if not all_employees:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(all_employees)
        
        # 提取需要的列
        base_col = f'grade_{base_year}'
        target_col = f'grade_{target_year}'
        
        # 确保这些列存在
        if base_col not in df.columns or target_col not in df.columns:
            return None
        
        # 筛选有效数据
        valid_df = df[df[base_col].notna() & df[target_col].notna()]
        
        # 创建晋升状态列
        def determine_status(row):
            if row[base_col] == row[target_col]:
                return '保持不变'
            
            base_grade = row[base_col]
            target_grade = row[target_col]
            
            # 简单的职级比较逻辑
            grade_order = {'G1': 1, 'G2': 2, 'G3': 3, 'G4A': 4, 'G4B': 5, 'Technian': 6}
            
            if base_grade in grade_order and target_grade in grade_order:
                if grade_order[target_grade] > grade_order[base_grade]:
                    return '晋升'
                else:
                    return '降级'
            
            return '其他变动'
        
        valid_df['status'] = valid_df.apply(determine_status, axis=1)
        
        # 计算不同状态的数量
        status_counts = valid_df['status'].value_counts()
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        wedges, texts, autotexts = ax.pie(
            status_counts, 
            labels=status_counts.index, 
            autopct='%1.1f%%',
            startangle=90,
            colors=['lightgreen', 'lightblue', 'salmon']
        )
        ax.axis('equal')
        ax.set_title(f'{base_year}年到{target_year}年职级变动分析')
        
        # 增加图例
        plt.legend(wedges, [f'{k}: {v}人' for k, v in status_counts.items()],
                   loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        return fig

class MatplotlibCanvas(FigureCanvas):
    """用于在PyQt5界面中嵌入Matplotlib图表的类"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(self.fig)
        self.setParent(parent)

    def update_figure(self, figure):
        """更新图表"""
        if figure:
            # 清除当前图表
            self.fig.clf()
            
            # 将新图表的内容复制到当前图表
            for ax in figure.get_axes():
                new_ax = self.fig.add_subplot(111)
                for line in ax.get_lines():
                    new_ax.plot(line.get_xdata(), line.get_ydata(), 
                                 color=line.get_color(), 
                                 marker=line.get_marker(),
                                 linestyle=line.get_linestyle(),
                                 linewidth=line.get_linewidth(),
                                 label=line.get_label())
                
                # 复制标题和标签
                new_ax.set_title(ax.get_title())
                new_ax.set_xlabel(ax.get_xlabel())
                new_ax.set_ylabel(ax.get_ylabel())
                
                # 复制网格
                new_ax.grid(ax.get_grid())
                
                # 复制图例
                if ax.get_legend():
                    new_ax.legend()
            
            self.fig.tight_layout()
            self.draw() 
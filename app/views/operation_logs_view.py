from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QTableView, QHeaderView, QTableWidgetItem
)
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem
from qfluentwidgets import (
    LineEdit, PushButton, CardWidget, FluentIcon, 
    InfoBar, InfoBarPosition, SearchLineEdit, ComboBox,
    CalendarPicker, TitleLabel, BodyLabel, TableWidget,
    Dialog
)
import datetime

class OperationLogsView(QWidget):
    """操作日志视图，用于显示系统操作日志"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent = parent
        
        # 初始化UI
        self.initUI()
        
        # 加载日志数据
        self.loadLogs()
    
    def initUI(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # 顶部工具栏
        top_bar = QHBoxLayout()
        
        # 标题
        title_label = TitleLabel("操作日志")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        # 搜索框
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("搜索日志")
        self.search_edit.textChanged.connect(self.filterLogs)
        self.search_edit.setFixedWidth(200)
        top_bar.addWidget(self.search_edit)
        
        # 操作类型筛选
        self.operation_filter = ComboBox(self)
        self.operation_filter.setPlaceholderText("所有操作")
        self.operation_filter.currentTextChanged.connect(self.filterLogs)
        self.operation_filter.setFixedWidth(150)
        top_bar.addWidget(self.operation_filter)
        
        # 日期范围 - 使用FluentUI风格的日期选择器
        date_container = QWidget(self)
        date_layout = QHBoxLayout(date_container)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(5)
        
        date_label_from = BodyLabel("从:", self)
        date_layout.addWidget(date_label_from)
        
        # 开始日期选择器
        self.start_date_picker = CalendarPicker(self)
        self.start_date_picker.setDate(QDateTime.currentDateTime().addDays(-30).date())
        self.start_date_picker.dateChanged.connect(self.filterLogs)
        date_layout.addWidget(self.start_date_picker)
        
        date_label_to = BodyLabel("到:", self)
        date_layout.addWidget(date_label_to)
        
        # 结束日期选择器
        self.end_date_picker = CalendarPicker(self)
        self.end_date_picker.setDate(QDateTime.currentDateTime().date())
        self.end_date_picker.dateChanged.connect(self.filterLogs)
        date_layout.addWidget(self.end_date_picker)
        
        top_bar.addWidget(date_container)
        
        # 刷新按钮
        self.refresh_btn = PushButton('刷新', self)
        self.refresh_btn.setIcon(FluentIcon.SYNC)
        self.refresh_btn.clicked.connect(self.loadLogs)
        top_bar.addWidget(self.refresh_btn)
        
        main_layout.addLayout(top_bar)
        
        # 表格卡片
        self.table_card = CardWidget(self)
        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(15, 15, 15, 15)
        
        # 日志表格
        self.logs_table = TableWidget(self)
        self.logs_table.setSelectionBehavior(TableWidget.SelectRows)
        self.logs_table.setEditTriggers(TableWidget.NoEditTriggers)
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.horizontalHeader().setHighlightSections(False)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels(['ID', '用户', '操作类型', '详情', '时间'])
        # 连接双击事件到显示详情
        self.logs_table.cellDoubleClicked.connect(self.showLogDetails)
        
        table_layout.addWidget(self.logs_table)
        
        main_layout.addWidget(self.table_card)
        
        # 底部状态栏
        bottom_bar = QHBoxLayout()
        
        self.status_label = BodyLabel("总计: 0 条日志记录")
        bottom_bar.addWidget(self.status_label)
        
        bottom_bar.addStretch()
        
        self.export_btn = PushButton('导出日志', self)
        self.export_btn.setIcon(FluentIcon.DOWNLOAD)
        self.export_btn.clicked.connect(self.exportLogs)
        bottom_bar.addWidget(self.export_btn)
        
        self.clear_btn = PushButton('清除筛选', self)
        self.clear_btn.setIcon(FluentIcon.CANCEL)
        self.clear_btn.clicked.connect(self.clearFilters)
        bottom_bar.addWidget(self.clear_btn)
        
        main_layout.addLayout(bottom_bar)
        
        self.setLayout(main_layout)
    
    def loadLogs(self):
        """加载日志数据"""
        # 保存当前列宽
        column_widths = []
        for i in range(5):  # 假设有5列
            if i < self.logs_table.columnCount():
                column_widths.append(self.logs_table.columnWidth(i))
        
        # 获取操作日志
        logs = self.db.get_operation_logs(limit=1000)
        
        # 清空现有数据
        self.logs_table.clearContents()
        self.logs_table.setRowCount(0)
        
        # 添加日志数据到表格
        for row, log in enumerate(logs):
            self.logs_table.insertRow(row)
            
            # 设置单元格数据
            self.logs_table.setItem(row, 0, QTableWidgetItem(str(log.get('id', ''))))
            self.logs_table.setItem(row, 1, QTableWidgetItem(str(log.get('user', ''))))
            self.logs_table.setItem(row, 2, QTableWidgetItem(str(log.get('operation', ''))))
            self.logs_table.setItem(row, 3, QTableWidgetItem(str(log.get('details', ''))))
            
            # 格式化时间戳，只显示到秒
            timestamp = log.get('timestamp', '')
            formatted_timestamp = self.formatTimestamp(timestamp)
            self.logs_table.setItem(row, 4, QTableWidgetItem(formatted_timestamp))
        
        # 更新状态栏
        self.status_label.setText(f"总计: {len(logs)} 条日志记录")
        
        # 更新操作类型下拉框
        self.updateOperationFilter(logs)
        
        # 如果之前存在列宽设置，则恢复
        if column_widths and len(column_widths) == 5:
            # 恢复之前保存的列宽
            for i in range(5):
                if i < self.logs_table.columnCount() and column_widths[i] > 0:
                    self.logs_table.setColumnWidth(i, column_widths[i])
        else:
            # 首次加载或列数变化时，自动调整列宽
            self.logs_table.setColumnWidth(0, 50)  # ID
            self.logs_table.setColumnWidth(1, 100)  # 用户
            self.logs_table.setColumnWidth(2, 150)  # 操作类型
            self.logs_table.setColumnWidth(4, 180)  # 时间
    
    def formatTimestamp(self, timestamp):
        """格式化时间戳，只显示到秒"""
        try:
            # 如果时间戳包含毫秒等信息，只保留到秒
            if timestamp and ' ' in timestamp:
                date_part, time_part = timestamp.split(' ', 1)
                if '.' in time_part:
                    time_part = time_part.split('.')[0]
                return f"{date_part} {time_part}"
            return timestamp
        except:
            return timestamp
    
    def updateOperationFilter(self, logs):
        """更新操作类型筛选下拉框"""
        # 获取所有操作类型
        operations = set()
        for log in logs:
            if log.get('operation'):
                operations.add(log.get('operation'))
        
        # 更新下拉框
        current_op = self.operation_filter.currentText()
        self.operation_filter.clear()
        self.operation_filter.addItem("所有操作")
        
        for op in sorted(operations):
            self.operation_filter.addItem(op)
        
        # 如果之前有选中的操作类型，则恢复选中
        if current_op and current_op in operations:
            self.operation_filter.setCurrentText(current_op)
    
    def filterLogs(self):
        """筛选日志"""
        search_text = self.search_edit.text().lower()
        operation_type = self.operation_filter.currentText()
        start_date = self.start_date_picker.getDate().toString("yyyy-MM-dd")
        end_date = self.end_date_picker.getDate().addDays(1).toString("yyyy-MM-dd")  # 加一天以包括结束当天
        
        # 遍历所有行，根据筛选条件决定是否显示
        for row in range(self.logs_table.rowCount()):
            show_row = True
            
            # 检查是否匹配搜索文本
            if search_text:
                text_match = False
                for col in range(1, self.logs_table.columnCount()):  # 跳过ID列
                    item = self.logs_table.item(row, col)
                    if item and search_text in item.text().lower():
                        text_match = True
                        break
                
                if not text_match:
                    show_row = False
            
            # 检查是否匹配操作类型
            if show_row and operation_type and operation_type != "所有操作":
                operation_item = self.logs_table.item(row, 2)  # 操作类型列
                if not operation_item or operation_item.text() != operation_type:
                    show_row = False
            
            # 检查是否在日期范围内
            if show_row:
                timestamp_item = self.logs_table.item(row, 4)  # 时间列
                if timestamp_item:
                    # 从格式化后的时间戳中提取日期部分
                    log_date = timestamp_item.text().split()[0] if ' ' in timestamp_item.text() else timestamp_item.text()
                    if log_date < start_date or log_date >= end_date:
                        show_row = False
            
            # 设置行的可见性
            self.logs_table.setRowHidden(row, not show_row)
        
        # 更新显示的记录数
        visible_count = sum(1 for row in range(self.logs_table.rowCount()) if not self.logs_table.isRowHidden(row))
        self.status_label.setText(f"显示: {visible_count} / {self.logs_table.rowCount()} 条日志记录")
    
    def clearFilters(self):
        """清除所有筛选条件"""
        self.search_edit.clear()
        self.operation_filter.setCurrentText("所有操作")
        
        # 重置日期范围
        self.start_date_picker.setDate(QDateTime.currentDateTime().addDays(-30).date())
        self.end_date_picker.setDate(QDateTime.currentDateTime().date())
        
        # 显示所有行
        for row in range(self.logs_table.rowCount()):
            self.logs_table.setRowHidden(row, False)
        
        # 更新状态栏
        self.status_label.setText(f"总计: {self.logs_table.rowCount()} 条日志记录")
    
    def exportLogs(self):
        """导出日志到CSV文件"""
        from PyQt5.QtWidgets import QFileDialog
        import csv
        
        # 获取保存文件路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "", "CSV 文件 (*.csv);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 确保文件有.csv扩展名
            if not file_path.endswith('.csv'):
                file_path += '.csv'
            
            # 打开文件写入
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                headers = []
                for col in range(self.logs_table.columnCount()):
                    headers.append(self.logs_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # 仅写入可见行
                for row in range(self.logs_table.rowCount()):
                    if not self.logs_table.isRowHidden(row):
                        row_data = []
                        for col in range(self.logs_table.columnCount()):
                            item = self.logs_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
            
            # 导出成功提示
            InfoBar.success(
                title='导出成功',
                content=f"日志已导出到 {file_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            # 导出失败提示
            InfoBar.error(
                title='导出失败',
                content=f"导出日志时发生错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def showLogDetails(self, row, column):
        """显示日志详情对话框"""
        # 获取当前行的数据
        log_id = self.logs_table.item(row, 0).text()
        user = self.logs_table.item(row, 1).text()
        operation = self.logs_table.item(row, 2).text()
        details = self.logs_table.item(row, 3).text()
        timestamp = self.logs_table.item(row, 4).text()
        
        # 构建详情内容
        title = f"日志详情 #{log_id}"
        content = f"""操作用户: {user}
操作类型: {operation}
操作时间: {timestamp}

详细信息:
{details}"""
        
        # 创建并显示对话框
        dialog = Dialog(title, content, self)
        dialog.setContentCopyable(True)  # 允许复制内容
        dialog.exec() 
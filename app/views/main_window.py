import sys
import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QFileDialog, 
    QMessageBox, QTabWidget, QSplitter
)
from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, 
    MSFluentWindow, FluentIcon, SearchLineEdit, 
    InfoBar, InfoBarPosition, LineEdit, PushButton, 
    ComboBox, ToggleButton, MessageBox, SplitTitleBar
)
from .employee_list_view import EmployeeListView
from .employee_detail_view import EmployeeDetailView
from .statistics_view import StatisticsView
from .operation_logs_view import OperationLogsView
from ..models.database import EmployeeDatabase

class MainWindow(MSFluentWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 数据库实例
        self.db = EmployeeDatabase()
        
        # 设置窗口属性
        self.setWindowTitle("员工管理系统")
        self.resize(1200, 800)
        
        # 创建子视图
        self.employee_list_view = EmployeeListView(self.db, self)
        self.employee_detail_view = EmployeeDetailView(self.db, self)
        self.statistics_view = StatisticsView(self.db, self)
        self.operation_logs_view = OperationLogsView(self.db, self)
        
        # 初始化界面
        self.initNavigation()
        self.initWindow()
        
        # 连接信号和槽
        self.setupConnections()
    
    def initNavigation(self):
        """初始化导航栏"""
        self.navigationInterface.setMinimumWidth(200)
        self.navigationInterface.setFixedWidth(230)
        
        # 添加导航项
        self.navigationInterface.addItem(
            routeKey='employees',
            text='员工管理',
            icon=FluentIcon.PEOPLE,
            onClick=lambda: self.switchTo(self.employee_list_view, 'employees')
        )
        
        self.navigationInterface.addItem(
            routeKey='statistics',
            text='统计分析',
            icon=FluentIcon.PIE_SINGLE,
            onClick=lambda: self.switchTo(self.statistics_view, 'statistics')
        )
        
        self.navigationInterface.addItem(
            routeKey='import',
            text='导入数据',
            icon=FluentIcon.DOWNLOAD,
            onClick=self.importData
        )
        
        self.navigationInterface.addItem(
            routeKey='export',
            text='导出数据',
            icon=FluentIcon.SAVE,
            onClick=self.exportData
        )
        
        # 添加底部导航项
        self.navigationInterface.addItem(
            routeKey='logs',
            text='操作日志',
            icon=FluentIcon.HISTORY,
            onClick=lambda: self.switchTo(self.operation_logs_view, 'logs'),
            position=NavigationItemPosition.BOTTOM
        )
        
        self.navigationInterface.addItem(
            routeKey='backup',
            text='备份与恢复',
            icon=FluentIcon.SAVE,
            onClick=self.showBackupOptions,
            position=NavigationItemPosition.BOTTOM
        )
        
        # 设置默认选中的导航项
        self.navigationInterface.setCurrentItem('employees')
    
    def initWindow(self):
        """初始化窗口布局"""
        # 设置中心部件
        self.stackedWidget.addWidget(self.employee_list_view)
        self.stackedWidget.addWidget(self.statistics_view)
        self.stackedWidget.addWidget(self.operation_logs_view)
        
        # 设置初始页面
        self.stackedWidget.setCurrentWidget(self.employee_list_view)
    
    def setupConnections(self):
        """设置信号和槽连接"""
        # 当选择员工时，显示员工详细信息
        self.employee_list_view.employeeSelected.connect(self.showEmployeeDetail)
    
    def switchTo(self, widget, routeKey):
        """切换到指定页面"""
        self.stackedWidget.setCurrentWidget(widget)
        self.navigationInterface.setCurrentItem(routeKey)
    
    def showEmployeeDetail(self, employee_id):
        """显示员工详细信息"""
        # 在右侧弹出或切换到员工详情页面
        self.employee_detail_view.loadEmployee(employee_id)
    
    def importData(self):
        """导入数据功能"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "", "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                result = self.db.import_from_excel(file_path, "管理员")
                if result and result.get('success'):
                    InfoBar.success(
                        title='导入成功',
                        content=f"成功导入 {result.get('added')} 条记录，跳过 {result.get('skipped')} 条记录",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
                    # 刷新员工列表
                    self.employee_list_view.refreshEmployeeList()
                else:
                    InfoBar.error(
                        title='导入失败',
                        content="导入过程中发生错误",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title='导入失败',
                    content=f"错误：{str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
    
    def exportData(self):
        """导出数据功能"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出文件", "", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                success = self.db.export_to_excel(file_path)
                if success:
                    InfoBar.success(
                        title='导出成功',
                        content=f"数据已成功导出到 {file_path}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title='导出失败',
                        content="导出过程中发生错误",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title='导出失败',
                    content=f"错误：{str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
    
    def showBackupOptions(self):
        """显示备份和恢复选项"""
        msgBox = MessageBox(
            '数据备份与恢复',
            '请选择要执行的操作',
            self
        )
        
        backupBtn = msgBox.addButton('备份数据库', MessageBox.YesRole)
        restoreBtn = msgBox.addButton('恢复数据库', MessageBox.NoRole)
        cancelBtn = msgBox.addButton('取消', MessageBox.RejectRole)
        
        msgBox.exec()
        
        if msgBox.clickedButton() == backupBtn:
            self.backupDatabase()
        elif msgBox.clickedButton() == restoreBtn:
            self.restoreDatabase()
    
    def backupDatabase(self):
        """备份数据库"""
        backup_dir = QFileDialog.getExistingDirectory(self, "选择备份目录")
        
        if backup_dir:
            try:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f"employee_db_backup_{timestamp}.sqlite")
                
                success, path = self.db.backup_database(backup_path)
                
                if success:
                    InfoBar.success(
                        title='备份成功',
                        content=f"数据库已备份到 {path}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
                else:
                    InfoBar.error(
                        title='备份失败',
                        content="备份过程中发生错误",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
            except Exception as e:
                InfoBar.error(
                    title='备份失败',
                    content=f"错误：{str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
    
    def restoreDatabase(self):
        """恢复数据库"""
        backup_file, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件", "", "SQLite 数据库 (*.sqlite)"
        )
        
        if backup_file:
            # 确认对话框
            reply = MessageBox(
                '确认恢复',
                '恢复数据库将覆盖当前所有数据，确定要继续吗？',
                self
            )
            yesBtn = reply.addButton('确定', MessageBox.YesRole)
            reply.addButton('取消', MessageBox.NoRole)
            
            reply.exec()
            
            if reply.clickedButton() == yesBtn:
                try:
                    success = self.db.restore_database(backup_file, "管理员")
                    
                    if success:
                        InfoBar.success(
                            title='恢复成功',
                            content="数据库已成功恢复，即将重启应用程序",
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=3000,
                            parent=self
                        )
                        
                        # 延迟 3 秒后重启应用
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(3000, self.restartApplication)
                    else:
                        InfoBar.error(
                            title='恢复失败',
                            content="恢复过程中发生错误",
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=5000,
                            parent=self
                        )
                except Exception as e:
                    InfoBar.error(
                        title='恢复失败',
                        content=f"错误：{str(e)}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=5000,
                        parent=self
                    )
    
    def restartApplication(self):
        """重启应用程序"""
        # 关闭数据库连接
        self.db.close()
        
        # 获取当前应用实例和命令行参数
        app = QApplication.instance()
        
        # 尝试以与当前进程相同的方式重启
        import os
        import sys
        os.execl(sys.executable, sys.executable, *sys.argv)
        
        # 如果上面的重启方法失败，至少关闭当前应用程序
        app.quit()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 关闭数据库连接
        self.db.close()
        super().closeEvent(event) 
import sys
import os
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QFileDialog, 
    QMessageBox, QStackedWidget, QFrame
)
from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, 
    MSFluentWindow, FluentIcon as FIF, SearchLineEdit, 
    InfoBar, InfoBarPosition, PushButton, 
    ComboBox, ToggleButton, MessageBox, setTheme, Theme, 
    isDarkTheme, NavigationAvatarWidget, ToolTipFilter,
    setCustomStyleSheet, CustomStyleSheet, ToolTipPosition,
    ToolButton, TransparentToolButton
)
from qframelesswindow import FramelessWindow, StandardTitleBar

from .employee_list_view import EmployeeListView
from .employee_detail_view import EmployeeDetailView
from .statistics_view import StatisticsView
from .operation_logs_view import OperationLogsView
from ..models.database import EmployeeDatabase
from ..utils.resource_loader import get_resource_path

class MainWindow(MSFluentWindow):
    """主窗口类 - 使用Fluent Design风格"""
    
    def __init__(self):
        super().__init__()
        
        # 数据库实例
        self.db = EmployeeDatabase()
        
        # 设置窗口属性
        self.setWindowTitle("员工管理系统")
        self.resize(1200, 800)
        self.setWindowIcon(QIcon(get_resource_path('app/resources/images/logo.png')))
        
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
        
        # 初始化样式表
        self.setQss()
    
    def initNavigation(self):
        """初始化导航栏"""
        # 设置导航栏宽度
        self.navigationInterface.setFixedWidth(260)
        self.navigationInterface.setMinimumWidth(48)
        
        # 设置导航栏标题
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=NavigationAvatarWidget('员工管理系统', '企业版 v1.0'),
            onClick=lambda: InfoBar.success(
                title='关于',
                content='员工管理系统 - 企业版 v1.0',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            ),
            position=NavigationItemPosition.TOP
        )
        
        # 添加导航项
        self.navigationInterface.addItem(
            routeKey='employees',
            icon=FIF.PEOPLE,
            text='员工管理',
            position=NavigationItemPosition.TOP,
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.employee_list_view)
        )
        
        self.navigationInterface.addItem(
            routeKey='statistics',
            icon=FIF.PIE_SINGLE,
            text='统计分析',
            position=NavigationItemPosition.TOP,
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.statistics_view)
        )
        
        # 添加数据操作项
        self.navigationInterface.addItem(
            routeKey='import',
            icon=FIF.DOWNLOAD,
            text='导入数据',
            position=NavigationItemPosition.TOP,
            onClick=self.importData
        )
        
        self.navigationInterface.addItem(
            routeKey='export',
            icon=FIF.SAVE,
            text='导出数据',
            position=NavigationItemPosition.TOP,
            onClick=self.exportData
        )
        
        # 添加底部导航项
        self.navigationInterface.addItem(
            routeKey='logs',
            icon=FIF.HISTORY,
            text='操作日志',
            position=NavigationItemPosition.BOTTOM,
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.operation_logs_view)
        )
        
        self.navigationInterface.addItem(
            routeKey='backup',
            icon=FIF.SAVE_AS,
            text='备份与恢复',
            position=NavigationItemPosition.BOTTOM,
            onClick=self.showBackupOptions
        )
        
        self.navigationInterface.addItem(
            routeKey='settings',
            icon=FIF.SETTING,
            text='系统设置',
            position=NavigationItemPosition.BOTTOM,
            onClick=self.showSettings
        )
        
        # 设置默认选中的导航项
        self.navigationInterface.setCurrentItem('employees')
    
    def initWindow(self):
        """初始化窗口布局"""
        # 添加视图到堆叠部件
        self.addSubInterface(self.employee_list_view, 'employees', '员工管理')
        self.addSubInterface(self.statistics_view, 'statistics', '统计分析')
        self.addSubInterface(self.operation_logs_view, 'logs', '操作日志')
        
        # 设置样式
        self.setStyleSheet("""
            MainWindow {
                background-color: --ThemeBackgroundColor;
            }
        """)
    
    def addSubInterface(self, widget, name, title):
        """添加子界面到主窗口"""
        self.stackedWidget.addWidget(widget)
        widget.setObjectName(name)
        
    def setupConnections(self):
        """设置信号和槽连接"""
        # 当选择员工时，显示员工详细信息
        self.employee_list_view.employeeSelected.connect(self.showEmployeeDetail)
    
    def showEmployeeDetail(self, employee_id):
        """显示员工详细信息"""
        # 直接加载员工详情
        self.employee_detail_view.loadEmployee(employee_id)
        
        # 每次显示时确保窗口位于正确的位置
        if self.employee_detail_view.isVisible():
            # 相对于主窗口居中
            pos = self.mapToGlobal(self.rect().center())
            pos.setX(pos.x() - self.employee_detail_view.width() // 2)
            pos.setY(pos.y() - self.employee_detail_view.height() // 2)
            self.employee_detail_view.move(pos)
    
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
        """显示备份选项"""
        # 创建对话框窗口
        dialog = MessageBox(
            '数据库备份与恢复',
            '请选择要执行的操作：',
            self
        )
        
        # 添加备份按钮
        backup_button = dialog.addButton('备份数据库', MessageBox.ButtonRole.YesRole)
        backup_button.clicked.connect(self.backupDatabase)
        
        # 添加恢复按钮
        restore_button = dialog.addButton('恢复数据库', MessageBox.ButtonRole.NoRole)
        restore_button.clicked.connect(self.restoreDatabase)
        
        # 添加取消按钮
        dialog.addButton('取消', MessageBox.ButtonRole.RejectRole)
        
        # 显示对话框
        dialog.exec()
    
    def showSettings(self):
        """显示设置界面"""
        InfoBar.info(
            title='系统设置',
            content="系统设置功能尚未实现",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def backupDatabase(self):
        """备份数据库"""
        # 获取备份文件路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择备份保存位置", "", "SQLite Database (*.sqlite);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # 执行备份
            import shutil
            db_path = self.db.get_db_path()
            shutil.copy2(db_path, file_path)
            
            InfoBar.success(
                title='备份成功',
                content=f"数据库已成功备份到 {file_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        except Exception as e:
            InfoBar.error(
                title='备份失败',
                content=f"备份数据库时发生错误: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
    
    def restoreDatabase(self):
        """恢复数据库"""
        # 显示警告
        dialog = MessageBox(
            '恢复数据库',
            '警告：恢复数据库将替换当前的所有数据，此操作不可撤销。确定要继续吗？',
            self
        )
        yes_button = dialog.addButton('确定', MessageBox.ButtonRole.YesRole)
        dialog.addButton('取消', MessageBox.ButtonRole.NoRole)
        
        if dialog.exec() == 0 and dialog.clickedButton() == yes_button:
            # 获取要恢复的数据库文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择要恢复的数据库文件", "", "SQLite Database (*.sqlite);;All Files (*)"
            )
            
            if not file_path:
                return
                
            try:
                # 执行恢复
                import shutil
                import os
                
                # 关闭数据库连接
                self.db.close_connection()
                
                # 备份当前数据库
                db_path = self.db.get_db_path()
                backup_path = db_path + ".bak"
                
                # 如果已有备份则删除
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                
                # 创建备份
                shutil.copy2(db_path, backup_path)
                
                # 替换数据库
                shutil.copy2(file_path, db_path)
                
                # 重新启动应用
                reply = MessageBox(
                    '恢复成功',
                    '数据库已成功恢复。需要重启应用以应用更改。是否立即重启？',
                    self
                )
                yes_button = reply.addButton('是', MessageBox.ButtonRole.YesRole)
                reply.addButton('否', MessageBox.ButtonRole.NoRole)
                
                if reply.exec() == 0 and reply.clickedButton() == yes_button:
                    self.restartApplication()
                
            except Exception as e:
                InfoBar.error(
                    title='恢复失败',
                    content=f"恢复数据库时发生错误: {str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
    
    def restartApplication(self):
        """重启应用"""
        QApplication.quit()
        # 重新启动应用
        import os, sys
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    def setQss(self):
        """设置样式表"""
        # 根据当前主题设置样式
        theme = 'dark' if isDarkTheme() else 'light'
        try:
            # 尝试从资源中加载样式表
            style_path = get_resource_path(f'app/resources/qss/{theme}/style.qss')
            if os.path.exists(style_path):
                with open(style_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception:
            # 如果加载失败，使用默认样式
            pass
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 关闭数据库连接
        self.db.close_connection()
        
        # 接受关闭事件
        event.accept() 
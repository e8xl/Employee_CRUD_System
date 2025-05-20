import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from app.models.database import EmployeeDatabase
from app.models.score_database import ScoreDatabase
from app.views.main_window import MainWindow


def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    # 判断是否为已编译的可执行文件
    if getattr(sys, 'frozen', False):
        # 如果是PyInstaller打包的可执行文件
        base_path = sys._MEIPASS
    else:
        # 如果是在开发环境中运行
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # 组合路径并返回
    return os.path.join(base_path, relative_path)


def main():
    """应用入口"""
    # 创建应用
    app = QApplication(sys.argv)

    # 应用名称
    app.setApplicationName("员工管理系统")
    app.setApplicationDisplayName("员工管理系统")

    # 设置图标
    icon_path = get_resource_path('app/resources/images/logo.png')
    app.setWindowIcon(QIcon(icon_path))

    # 加载CSS样式
    try:
        style_path = get_resource_path('app/resources/qss/light/style.qss')
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())
    except Exception as e:
        print(f"加载样式表失败: {e}")

    # 连接数据库
    db = EmployeeDatabase("employee_db.sqlite")
    score_db = ScoreDatabase("employee_db.sqlite")

    # 创建并显示主窗口
    window = MainWindow(db, score_db)

    # 设置默认显示员工管理页面，导航栏也选中员工管理项
    window.navigationInterface.setCurrentItem('employees')
    window.stackedWidget.setCurrentWidget(window.employee_list_view)

    window.show()

    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

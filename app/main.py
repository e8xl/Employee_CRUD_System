import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from qfluentwidgets import setTheme, Theme
from app.views.main_window import MainWindow

def main():
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("员工管理系统")
    
    # 设置应用主题
    setTheme(Theme.AUTO)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
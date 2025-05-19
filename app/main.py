import sys
import os
from PyQt5.QtCore import QTranslator, QLocale
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QCoreApplication
from qfluentwidgets import setTheme, Theme, setThemeColor, InfoBar, InfoBarPosition, FluentTranslator
from app.views.main_window import MainWindow
from app.models.database import EmployeeDatabase
from app.models.score_database import ScoreDatabase

def main():
    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setApplicationName("员工管理系统")
    app.setOrganizationName("Siemens")
    
    # 设置翻译器
    translator = FluentTranslator(QLocale())
    app.installTranslator(translator)
    
    # 设置应用主题
    setTheme(Theme.AUTO)
    setThemeColor('#0078d4')  # Fluent设计蓝色主题
    
    # 创建数据库实例
    db = EmployeeDatabase()
    
    # 创建成绩数据库实例
    score_db = ScoreDatabase()
    
    # 数据迁移
    try:
        # 如果系统是第一次使用新的职级历史功能，提示用户迁移数据
        db.cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='employee_grades'")
        table_exists = db.cursor.fetchone()[0] > 0
        
        if table_exists:
            db.cursor.execute("SELECT count(*) FROM employee_grades")
            records_count = db.cursor.fetchone()[0]
            
            if records_count == 0:
                # 表存在但没有记录，需要迁移
                migrated_count = db.migrate_existing_grades()
                if migrated_count > 0:
                    print(f"成功迁移{migrated_count}条职级记录")
    except Exception as e:
        print(f"数据迁移错误: {e}")
    
    # 创建主窗口
    window = MainWindow(db, score_db)
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
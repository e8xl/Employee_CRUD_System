#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
初始化数据库和表结构
"""

import importlib.util
import os
import sys

def import_module_from_file(file_path):
    """从文件导入模块"""
    module_name = os.path.basename(file_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    """主函数"""
    print("开始初始化系统...")
    
    # 1. 创建员工数据库和导入员工数据
    print("\n步骤1: 创建员工数据库和导入员工数据")
    try:
        create_db_module = import_module_from_file('create_employee_db.py')
        create_db_module.create_new_database()
        print("✓ 员工数据库创建成功")
    except Exception as e:
        print(f"× 员工数据库创建失败: {e}")
        return
    
    # 2. 创建成绩管理系统表
    print("\n步骤2: 创建成绩管理系统表")
    try:
        create_score_tables_module = import_module_from_file('create_score_tables.py')
        create_score_tables_module.create_score_tables()
        print("✓ 成绩管理系统表创建成功")
    except Exception as e:
        print(f"× 成绩管理系统表创建失败: {e}")
        
    # 3. 迁移职级数据
    print("\n步骤3: 迁移职级历史数据")
    try:
        migrate_grades_module = import_module_from_file('migrate_employee_grades.py')
        result = migrate_grades_module.migrate_employee_grades()
        if result:
            print("✓ 职级历史数据迁移成功")
        else:
            print("× 职级历史数据迁移过程中出现错误")
    except Exception as e:
        print(f"× 职级历史数据迁移失败: {e}")
    
    print("\n初始化完成! 现在可以运行 python run.py 启动系统")

if __name__ == "__main__":
    main() 
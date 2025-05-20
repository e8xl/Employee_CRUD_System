#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
初始化AUT部门成绩录入系统
此脚本执行以下任务:
1. 更新数据库结构，添加必要的表和字段
2. 添加手焊技能和其他技能项目
"""

import os
import sys
import time
import sqlite3

def print_step(step, message):
    """打印带格式的步骤信息"""
    print(f"\n[步骤 {step}] {message}")
    print("=" * 60)

def main():
    print("\n" + "=" * 60)
    print("欢迎使用AUT部门成绩录入系统初始化工具")
    print("本工具将更新数据库并配置必要的项目")
    print("=" * 60 + "\n")
    
    # 检查数据库是否存在
    if not os.path.exists('employee_db.sqlite'):
        print("错误: 未找到员工数据库文件。请先运行run_init.py创建基础数据库。")
        return False
    
    # 步骤1: 更新数据库结构
    print_step(1, "更新数据库结构")
    from update_aut_db import update_database
    if not update_database():
        print("数据库结构更新失败，退出程序。")
        return False
    
    # 短暂暂停，确保数据库操作完成
    time.sleep(1)
    
    # 步骤2: 添加手焊技能和其他技能项目
    print_step(2, "添加手焊技能和其他技能项目")
    from add_hand_solder_item import add_hand_solder_item
    if not add_hand_solder_item():
        print("添加技能项目失败，退出程序。")
        return False
    
    # 完成
    print("\n" + "=" * 60)
    print("初始化完成！")
    print("现在您可以运行系统并使用AUT部门成绩录入功能了。")
    print("=" * 60 + "\n")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 
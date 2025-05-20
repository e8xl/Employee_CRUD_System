#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新数据库脚本 - 为AUT部门职级计算添加必要的数据结构
"""

import sqlite3
import sys
import os

def update_database():
    """更新数据库结构"""
    print("正在更新数据库结构...")
    
    # 连接数据库
    conn = sqlite3.connect('employee_db.sqlite')
    cursor = conn.cursor()
    
    try:
        # 1. 检查department_assessment_items表是否有category字段
        cursor.execute("PRAGMA table_info(department_assessment_items)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category' not in columns:
            print("添加category字段到department_assessment_items表...")
            cursor.execute('''
            ALTER TABLE department_assessment_items
            ADD COLUMN category TEXT DEFAULT '岗位技能'
            ''')
            conn.commit()
            print("成功添加category字段")
        else:
            print("category字段已存在")
        
        # 2. 创建employee_score_details表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_score_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_no TEXT NOT NULL,
            assessment_year INTEGER NOT NULL,
            detail_key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(employee_no, assessment_year, detail_key)
        )
        ''')
        conn.commit()
        print("成功创建employee_score_details表")
        
        # 3. 更新AUT部门考核项目的类别
        print("更新AUT部门考核项目类别...")
        
        # 首先查询所有AUT部门考核项目
        cursor.execute("SELECT id, assessment_name FROM department_assessment_items WHERE department = 'AUT'")
        items = cursor.fetchall()
        
        # 定义手焊技能项目名称
        hand_solder_name = "手焊"
        
        # 定义其他技能项目名称
        other_skills = {
            "通用技能": ["通用技能"],
            "跨部门技能": ["跨部门技能"],
            "技师技能": ["技师技能"],
            "管理技能": ["管理技能"]
        }
        
        # 更新项目类别
        for item_id, name in items:
            category = "岗位技能"  # 默认类别
            
            # 判断是否是手焊技能
            if hand_solder_name in name:
                category = "手焊技能"
            
            # 判断是否是其他技能
            for cat, keywords in other_skills.items():
                if any(keyword in name for keyword in keywords):
                    category = cat
                    break
            
            # 更新类别
            cursor.execute(
                "UPDATE department_assessment_items SET category = ? WHERE id = ?",
                (category, item_id)
            )
        
        conn.commit()
        print(f"已更新{len(items)}个考核项目的类别")
        
        print("数据库结构更新完成！")
        
    except sqlite3.Error as e:
        print(f"数据库更新失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    update_database() 
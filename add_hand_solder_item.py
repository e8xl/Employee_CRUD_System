#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加手焊技能考核项目到AUT部门
"""

import sqlite3
import sys
import os

def add_hand_solder_item():
    """添加手焊技能考核项目"""
    print("正在添加手焊技能考核项目...")
    
    # 连接数据库
    conn = sqlite3.connect('employee_db.sqlite')
    cursor = conn.cursor()
    
    try:
        # 检查是否已存在手焊技能项目
        cursor.execute("""
        SELECT id FROM department_assessment_items 
        WHERE department = 'AUT' AND assessment_name = '手焊技能' AND category = '手焊技能'
        """)
        
        existing = cursor.fetchone()
        
        if existing:
            print("手焊技能项目已存在，ID:", existing[0])
            return True
        
        # 添加手焊技能项目
        cursor.execute("""
        INSERT INTO department_assessment_items 
        (department, assessment_name, weight, max_score, category) 
        VALUES ('AUT', '手焊技能', 0.1, 4, '手焊技能')
        """)
        
        conn.commit()
        print("成功添加手焊技能考核项目")
        
        # 添加其他技能项目
        other_skills = [
            ('通用技能', 0.2, 100, '通用技能'),
            ('跨部门技能', 0.1, 100, '跨部门技能'),
            ('技师技能', 0.1, 100, '技师技能'),
            ('管理技能', 0.1, 100, '管理技能')
        ]
        
        for name, weight, max_score, category in other_skills:
            # 检查是否已存在
            cursor.execute("""
            SELECT id FROM department_assessment_items 
            WHERE department = 'AUT' AND assessment_name = ? AND category = ?
            """, (name, category))
            
            if cursor.fetchone():
                print(f"{name}项目已存在")
                continue
            
            # 添加项目
            cursor.execute("""
            INSERT INTO department_assessment_items 
            (department, assessment_name, weight, max_score, category) 
            VALUES ('AUT', ?, ?, ?, ?)
            """, (name, weight, max_score, category))
            
            print(f"成功添加{name}考核项目")
        
        conn.commit()
        print("所有技能项目添加完成！")
        
    except sqlite3.Error as e:
        print(f"添加手焊技能项目失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    add_hand_solder_item() 
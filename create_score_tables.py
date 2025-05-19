#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os

def create_score_tables():
    """创建成绩管理系统所需的表结构"""
    
    # 连接到数据库
    conn = sqlite3.connect('employee_db.sqlite')
    cursor = conn.cursor()
    
    # 创建部门考核项目表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS department_assessment_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department TEXT NOT NULL,
        assessment_name TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        max_score REAL DEFAULT 100.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(department, assessment_name)
    )
    ''')
    
    # 创建部门职级计算公式表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS department_grade_formulas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department TEXT NOT NULL UNIQUE,
        formula TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建员工考核成绩表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employee_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_no TEXT NOT NULL,
        assessment_year INTEGER NOT NULL,
        assessment_item_id INTEGER NOT NULL,
        score REAL NOT NULL,
        comment TEXT,
        created_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (assessment_item_id) REFERENCES department_assessment_items(id) ON DELETE CASCADE,
        UNIQUE(employee_no, assessment_year, assessment_item_id)
    )
    ''')
    
    # 创建预测职级表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predicted_grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_no TEXT NOT NULL,
        assessment_year INTEGER NOT NULL,
        current_grade TEXT NOT NULL,
        predicted_grade TEXT NOT NULL,
        total_score REAL NOT NULL,
        calculation_details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(employee_no, assessment_year)
    )
    ''')
    
    # 创建员工职级历史表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employee_grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_no TEXT NOT NULL,
        year INTEGER NOT NULL,
        grade TEXT NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(employee_no, year)
    )
    ''')
    
    # 加入示例数据
    try:
        # 添加一些示例部门
        departments = ['AUT', 'CD-FID', 'CD-Sensor', 'FS-Detector', 'FS-Module', 'FS-Panel', 'FS-Sounder', 'SMT', 'THT']
        
        # 添加一些示例考核项目
        assessment_items = [
            ('技术水平', 2.0, 100.0),
            ('工作质量', 1.5, 100.0),
            ('团队协作', 1.0, 100.0),
            ('工作态度', 1.0, 100.0),
            ('创新能力', 1.5, 100.0)
        ]
        
        # 为每个部门添加考核项目
        for dept in departments:
            for item_name, weight, max_score in assessment_items:
                cursor.execute('''
                INSERT OR IGNORE INTO department_assessment_items 
                (department, assessment_name, weight, max_score)
                VALUES (?, ?, ?, ?)
                ''', (dept, item_name, weight, max_score))
        
        # 添加一些示例职级计算公式
        for dept in departments:
            formula = {
                'grade_thresholds': [
                    {'grade': 'G1', 'min_score': 0, 'max_score': 60},
                    {'grade': 'G2', 'min_score': 61, 'max_score': 75},
                    {'grade': 'G3', 'min_score': 76, 'max_score': 85},
                    {'grade': 'G4A', 'min_score': 86, 'max_score': 93},
                    {'grade': 'G4B', 'min_score': 94, 'max_score': 100}
                ]
            }
            
            import json
            cursor.execute('''
            INSERT OR IGNORE INTO department_grade_formulas
            (department, formula, description)
            VALUES (?, ?, ?)
            ''', (dept, json.dumps(formula), f"{dept}部门职级计算公式"))
            
        # 记录操作日志
        cursor.execute('''
        INSERT INTO operation_logs (user, operation, details)
        VALUES (?, ?, ?)
        ''', ('系统', '创建成绩管理表', '创建成绩管理系统所需的表结构并添加示例数据'))
        
        # 提交更改
        conn.commit()
        print("成功创建成绩管理系统表结构并添加示例数据")
            
    except Exception as e:
        print(f"添加示例数据时出错: {e}")
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    create_score_tables()
    print("成绩管理系统表结构创建完成") 
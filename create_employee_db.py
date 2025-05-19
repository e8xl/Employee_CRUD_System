#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
import os

def create_new_database():
    """创建全新的员工数据库，使用名字、GID和员工编号作为唯一标识"""
    
    # 删除现有数据库文件（如果存在）
    if os.path.exists('employee_db.sqlite'):
        os.rename('employee_db.sqlite', 'employee_db.sqlite.backup')
        print(f"原数据库已备份为: employee_db.sqlite.backup")
    
    # 连接到新数据库
    conn = sqlite3.connect('employee_db.sqlite')
    cursor = conn.cursor()
    
    # 创建员工表，不使用自增ID作为主键
    cursor.execute('''
    CREATE TABLE employees (
        employee_no TEXT NOT NULL,
        gid TEXT NOT NULL,
        name TEXT NOT NULL,
        status TEXT,
        department TEXT,
        grade_2022 TEXT,
        grade_2023 TEXT,
        grade_2024 TEXT,
        grade_2025 TEXT,
        notes TEXT,
        PRIMARY KEY (employee_no, gid, name)
    )
    ''')
    
    # 创建操作日志表
    cursor.execute('''
    CREATE TABLE operation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        operation TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 提交更改
    conn.commit()
    
    # 导入CSV数据
    try:
        # 读取CSV文件
        df = pd.read_csv('data/2025最新车间员工数据.csv', encoding='utf-8')
        
        # 重命名列以匹配数据库表结构
        column_mapping = {
            'Status': 'status',
            'GID': 'gid',
            'Personal Number': 'employee_no',
            'Chinese Name': 'name',
            '2022 Skill Level': 'grade_2022',
            '2023 Skill Level': 'grade_2023',
            '2024 Skill Level': 'grade_2024',
            '2025 Skill Level': 'grade_2025',
            'Company department': 'department'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 只选择需要的列
        required_columns = ['status', 'gid', 'employee_no', 'name', 'grade_2022', 
                         'grade_2023', 'grade_2024', 'grade_2025', 'department']
        
        # 检查所需列是否都存在
        for col in required_columns:
            if col not in df.columns:
                print(f"警告: CSV中缺少列 '{col}'")
        
        # 过滤出有效列
        valid_columns = [col for col in required_columns if col in df.columns]
        df = df[valid_columns]
        
        # 填充空值
        df = df.fillna('')
        
        # 导入数据
        for _, row in df.iterrows():
            # 组装SQL参数
            columns = ', '.join(valid_columns)
            placeholders = ', '.join(['?'] * len(valid_columns))
            
            # 准备数据
            data = tuple(row[col] for col in valid_columns)
            
            # 插入数据
            cursor.execute(f"INSERT INTO employees ({columns}) VALUES ({placeholders})", data)
        
        # 记录操作日志
        cursor.execute('''
        INSERT INTO operation_logs (user, operation, details)
        VALUES (?, ?, ?)
        ''', ('系统', '导入员工数据', f'从CSV文件导入了{len(df)}条员工记录'))
        
        # 提交更改
        conn.commit()
        print(f"成功导入 {len(df)} 条员工记录")
        
    except Exception as e:
        print(f"导入CSV数据时出错: {e}")
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    create_new_database()
    print("数据库创建和数据导入完成") 
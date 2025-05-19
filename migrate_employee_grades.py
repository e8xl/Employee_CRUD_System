#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import sys

def migrate_employee_grades():
    """将员工表中的职级数据迁移到职级历史表中"""
    try:
        # 连接到数据库
        conn = sqlite3.connect('employee_db.sqlite')
        cursor = conn.cursor()
        
        # 检查employees表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        if not cursor.fetchone():
            print("错误：employees表不存在")
            return
            
        # 检查employee_grades表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employee_grades'")
        if not cursor.fetchone():
            print("错误：employee_grades表不存在")
            return
            
        # 获取所有员工记录
        cursor.execute("SELECT * FROM employees")
        employees = cursor.fetchall()
        
        # 获取列名
        column_names = [desc[0] for desc in cursor.description]
        
        # 统计迁移情况
        migrated_count = 0
        skipped_count = 0
        
        # 处理每个员工
        for employee in employees:
            # 转换为字典，方便查找字段
            emp_dict = dict(zip(column_names, employee))
            employee_no = emp_dict['employee_no']
            
            # 查找年份对应的职级字段
            for year in range(2020, 2026):  # 从2020年到2025年
                grade_field = f'grade_{year}'
                
                if grade_field in emp_dict and emp_dict[grade_field]:
                    grade_value = emp_dict[grade_field]
                    
                    # 跳过空值
                    if not grade_value or grade_value.strip() == '':
                        skipped_count += 1
                        continue
                    
                    # 将职级数据插入employee_grades表
                    try:
                        cursor.execute("""
                        INSERT OR IGNORE INTO employee_grades
                        (employee_no, year, grade, comment)
                        VALUES (?, ?, ?, ?)
                        """, (employee_no, year, grade_value, "从员工表迁移的历史职级"))
                        
                        if cursor.rowcount > 0:
                            migrated_count += 1
                        else:
                            skipped_count += 1
                    except sqlite3.Error as e:
                        print(f"职级数据迁移错误 (员工: {employee_no}, 年份: {year}): {e}")
        
        # 提交事务
        conn.commit()
        
        # 记录操作日志
        cursor.execute("""
        INSERT INTO operation_logs (user, operation, details)
        VALUES (?, ?, ?)
        """, ('系统', '职级数据迁移', f'将员工表中的职级数据迁移到职级历史表，成功迁移 {migrated_count} 条记录，跳过 {skipped_count} 条记录'))
        
        conn.commit()
        
        print(f"职级数据迁移完成: 成功迁移 {migrated_count} 条记录，跳过 {skipped_count} 条记录")
        return True
        
    except Exception as e:
        print(f"职级数据迁移过程中发生错误: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_employee_grades() 
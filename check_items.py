#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys

def check_assessment_items():
    """检查所有考核项目"""
    # 连接数据库
    sys.stdout.write("正在连接数据库...\n")
    sys.stdout.flush()
    
    conn = sqlite3.connect('employee_db.sqlite')
    cursor = conn.cursor()
    
    try:
        # 检查数据库连接
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='department_assessment_items'")
        if not cursor.fetchone():
            sys.stdout.write("错误：考核项目表不存在！\n")
            sys.stdout.flush()
            return False
        
        sys.stdout.write("数据库连接成功，表存在\n")
        sys.stdout.flush()
        
        # 查询所有部门
        cursor.execute("SELECT DISTINCT department FROM department_assessment_items")
        departments = [row[0] for row in cursor.fetchall()]
        
        if not departments:
            sys.stdout.write("没有找到任何部门的考核项目\n")
            sys.stdout.flush()
            return True
            
        sys.stdout.write(f"找到以下部门: {', '.join(departments)}\n")
        sys.stdout.flush()
        
        # 统计每个部门的项目数量
        for dept in departments:
            cursor.execute("SELECT COUNT(*) FROM department_assessment_items WHERE department = ?", (dept,))
            count = cursor.fetchone()[0]
            sys.stdout.write(f"部门 {dept} 有 {count} 个考核项目\n")
            sys.stdout.flush()
        
        # 删除非AUT部门的考核项目
        sys.stdout.write("正在删除非AUT部门的考核项目...\n")
        sys.stdout.flush()
        cursor.execute("DELETE FROM department_assessment_items WHERE department != 'AUT'")
        
        # 获取删除的行数
        deleted_count = cursor.rowcount
        sys.stdout.write(f"已删除 {deleted_count} 个非AUT部门的考核项目\n")
        sys.stdout.flush()
        
        # 提交事务
        conn.commit()
        
        # 再次检查部门和项目数量
        cursor.execute("SELECT DISTINCT department FROM department_assessment_items")
        departments = [row[0] for row in cursor.fetchall()]
        
        sys.stdout.write(f"删除后剩余部门: {', '.join(departments)}\n")
        sys.stdout.flush()
        
        # 统计每个部门的项目数量
        for dept in departments:
            cursor.execute("SELECT COUNT(*) FROM department_assessment_items WHERE department = ?", (dept,))
            count = cursor.fetchone()[0]
            sys.stdout.write(f"部门 {dept} 有 {count} 个考核项目\n")
            sys.stdout.flush()
        
        sys.stdout.write("\n操作完成！\n")
        sys.stdout.flush()
        return True
        
    except Exception as e:
        # 发生错误时回滚事务
        conn.rollback()
        sys.stdout.write(f"错误：{e}\n")
        sys.stdout.flush()
        return False
    finally:
        # 关闭数据库连接
        conn.close()
        sys.stdout.write("数据库连接已关闭\n")
        sys.stdout.flush()

if __name__ == "__main__":
    sys.stdout.write("开始检查考核项目...\n")
    sys.stdout.flush()
    result = check_assessment_items()
    sys.stdout.write(f"操作结果: {'成功' if result else '失败'}\n")
    sys.stdout.flush()
    sys.stdout.write("脚本执行结束\n")
    sys.stdout.flush() 
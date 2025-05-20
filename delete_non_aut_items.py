#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys

print("脚本开始执行...")

def delete_non_aut_items():
    """删除除AUT部门以外的所有考核项目"""
    # 连接数据库
    print("正在连接数据库...")
    conn = sqlite3.connect('employee_db.sqlite')
    cursor = conn.cursor()
    
    try:
        # 检查数据库连接
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='department_assessment_items'")
        if not cursor.fetchone():
            print("错误：考核项目表不存在！")
            return False
        
        print("数据库连接成功，表存在")
            
        # 查询所有非AUT部门
        cursor.execute("SELECT DISTINCT department FROM department_assessment_items WHERE department != 'AUT'")
        departments = [row[0] for row in cursor.fetchall()]
        
        if not departments:
            print("没有找到除AUT之外的其他部门考核项目")
            return True
            
        print(f"找到以下非AUT部门: {', '.join(departments)}")
        
        # 统计要删除的项目数量
        cursor.execute("SELECT COUNT(*) FROM department_assessment_items WHERE department != 'AUT'")
        item_count = cursor.fetchone()[0]
        print(f"将要删除的考核项目总数: {item_count}")
        
        # 删除所有非AUT部门的考核项目
        print("正在删除非AUT部门的考核项目...")
        cursor.execute("DELETE FROM department_assessment_items WHERE department != 'AUT'")
        
        # 获取删除的行数
        deleted_count = cursor.rowcount
        print(f"已删除 {deleted_count} 个考核项目")
        
        # 提交事务
        conn.commit()
        
        # 3. 尝试记录操作日志
        try:
            # 检查操作日志表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operation_logs'")
            if cursor.fetchone():
                log_sql = """
                INSERT INTO operation_logs (user, operation, details)
                VALUES (?, ?, ?)
                """
                cursor.execute(log_sql, ('系统管理员', '删除考核项目', f'删除非AUT部门考核项目：共{deleted_count}个，涉及部门：{", ".join(departments)}'))
                conn.commit()
                print("已记录操作日志")
            else:
                print("操作日志表不存在，跳过记录日志")
        except Exception as e:
            print(f"记录日志时出错: {e}")
        
        print("\n操作完成！\n")
        return True
        
    except Exception as e:
        # 发生错误时回滚事务
        conn.rollback()
        print(f"错误：{e}")
        return False
    finally:
        # 关闭数据库连接
        conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    print("开始删除非AUT部门考核项目...")
    result = delete_non_aut_items()
    print(f"删除结果: {'成功' if result else '失败'}")
    print("脚本执行结束") 
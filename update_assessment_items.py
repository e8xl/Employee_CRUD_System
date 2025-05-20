#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys

print("脚本开始执行...")

def update_assessment_items():
    """更新AUT部门考核项目"""
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
            
        # 1. 删除AUT部门的所有考核项目
        print("正在删除AUT部门现有考核项目...")
        cursor.execute("DELETE FROM department_assessment_items WHERE department = 'AUT'")
        
        # 获取删除的行数
        deleted_count = cursor.rowcount
        print(f"已删除 {deleted_count} 个考核项目")
        
        # 2. 添加新的考核项目
        new_items = [
            "RUB", "USB", "AQR", "ODP", "RU46", "RUA3", "POL822", "QAA1181", "PXM10", 
            "RUS2", "DLS", "POL824", "老SOC", "ATEC老", "ATEC新", "Dimmer", "RWD", "RL100", 
            "BSG", "QAE", "UBC", "0SN300.BA", "POL895", "POL871", "RWR", "PPM", "QFM", 
            "Smart", "新M3", "POL935", "POL937", "POL966", "POL400", "ECV2", "POL900", 
            "FDB", "新SOC", "PXC4", "POL466", "PXC", "POL46X", "POL224", "POL95E", 
            "RAA/B", "RUW", "手焊", "Hotbar", "自动焊接", "标签打印", "机械臂", "自动镭雕"
        ]
        
        print(f"正在添加 {len(new_items)} 个新考核项目...")
        
        # 准备SQL语句和参数
        sql = """
        INSERT INTO department_assessment_items 
            (department, assessment_name, weight, max_score) 
        VALUES (?, ?, ?, ?)
        """
        
        # 为每个项目设置相同的权重和最高分
        weight = 1.0 / len(new_items)  # 平均分配权重，总和为1
        max_score = 4.0  # 最高分为4分
        
        print(f"单个项目权重: {weight}, 最高分: {max_score}")
        
        # 批量插入数据
        added_count = 0
        for item in new_items:
            try:
                cursor.execute(sql, ('AUT', item, weight, max_score))
                added_count += 1
                if added_count % 10 == 0:
                    print(f"已添加 {added_count} 个项目...")
            except Exception as e:
                print(f"添加项目 '{item}' 时出错: {e}")
        
        # 提交事务
        conn.commit()
        print(f"成功添加 {added_count} 个考核项目")
        
        # 3. 尝试记录操作日志
        try:
            # 检查操作日志表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operation_logs'")
            if cursor.fetchone():
                log_sql = """
                INSERT INTO operation_logs (user, operation, details)
                VALUES (?, ?, ?)
                """
                cursor.execute(log_sql, ('系统管理员', '更新考核项目', f'更新AUT部门考核项目：删除{deleted_count}个，添加{added_count}个'))
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
    print("开始更新AUT部门考核项目...")
    result = update_assessment_items()
    print(f"更新结果: {'成功' if result else '失败'}")
    print("脚本执行结束") 
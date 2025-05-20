#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import json

def update_aut_scoring_system():
    """更新AUT部门的评分系统和职级计算方法"""
    # 连接数据库
    print("正在连接数据库...")
    conn = sqlite3.connect('employee_db.sqlite')
    cursor = conn.cursor()
    
    try:
        # 检查数据库表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='department_assessment_items'")
        if not cursor.fetchone():
            print("错误：考核项目表不存在！")
            return False
        
        # 检查department_grade_formulas表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='department_grade_formulas'")
        if not cursor.fetchone():
            print("错误：职级计算公式表不存在！")
            # 创建表
            cursor.execute('''
            CREATE TABLE department_grade_formulas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT NOT NULL UNIQUE,
                formula TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
            print("已创建职级计算公式表")
        
        print("数据库连接成功，表存在")
        
        # 1. 添加分类字段（如果不存在）
        try:
            cursor.execute("SELECT category FROM department_assessment_items LIMIT 1")
        except sqlite3.OperationalError:
            print("添加category字段到考核项目表...")
            cursor.execute("ALTER TABLE department_assessment_items ADD COLUMN category TEXT DEFAULT '岗位技能'")
            conn.commit()
            print("成功添加category字段")
        
        # 2. 更新AUT部门考核项目的分类
        print("更新AUT部门考核项目分类...")
        
        # 先将所有AUT部门项目设为岗位技能类别
        cursor.execute("UPDATE department_assessment_items SET category = '岗位技能' WHERE department = 'AUT'")
        
        # 更新"手焊"项目的分类和权重
        cursor.execute("""
        UPDATE department_assessment_items 
        SET category = '手焊技能', weight = 0.1
        WHERE department = 'AUT' AND assessment_name = '手焊'
        """)
        
        # 更新其他岗位技能项目的权重
        # 首先获取有多少个岗位技能项目（不包括手焊）
        cursor.execute("SELECT COUNT(*) FROM department_assessment_items WHERE department = 'AUT' AND category = '岗位技能' AND assessment_name != '手焊'")
        skill_count = cursor.fetchone()[0]
        
        # 计算每个岗位技能项目的权重（总权重0.6除以项目数量）
        if skill_count > 0:
            single_weight = 0.6 / skill_count
            cursor.execute("""
            UPDATE department_assessment_items 
            SET weight = ?
            WHERE department = 'AUT' AND category = '岗位技能' AND assessment_name != '手焊'
            """, (single_weight,))
        
        # 3. 添加其他技能类别的项目
        additional_skills = [
            {'name': '通用技能', 'max_score': 100.0, 'weight': 0.2},
            {'name': '跨部门技能', 'max_score': 100.0, 'weight': 0.1},
            {'name': '技师技能', 'max_score': 100.0, 'weight': 0.1},
            {'name': '管理技能', 'max_score': 100.0, 'weight': 0.1}
        ]
        
        # 检查是否已存在，如果存在则更新，不存在则添加
        for skill in additional_skills:
            cursor.execute("""
            SELECT id FROM department_assessment_items 
            WHERE department = 'AUT' AND assessment_name = ? AND category = ?
            """, (skill['name'], skill['name']))
            
            result = cursor.fetchone()
            if result:
                cursor.execute("""
                UPDATE department_assessment_items 
                SET weight = ?, max_score = ?
                WHERE id = ?
                """, (skill['weight'], skill['max_score'], result[0]))
                print(f"更新 {skill['name']} 项目")
            else:
                cursor.execute("""
                INSERT INTO department_assessment_items 
                (department, assessment_name, category, weight, max_score)
                VALUES (?, ?, ?, ?, ?)
                """, ('AUT', skill['name'], skill['name'], skill['weight'], skill['max_score']))
                print(f"添加 {skill['name']} 项目")
        
        # 4. 更新AUT部门的职级计算公式
        grade_formula = {
            'formula_type': 'threshold',
            'description': 'AUT部门职级计算公式',
            'skill_categories': [
                {'name': '岗位技能', 'weight': 0.6, 'total_score': 204.0},
                {'name': '手焊技能', 'weight': 0.1, 'total_score': 4.0},
                {'name': '通用技能', 'weight': 0.2, 'total_score': 100.0},
                {'name': '跨部门技能', 'weight': 0.1, 'total_score': 100.0},
                {'name': '技师技能', 'weight': 0.1, 'total_score': 100.0},
                {'name': '管理技能', 'weight': 0.1, 'total_score': 100.0}
            ],
            'grade_thresholds': [
                {
                    'grade': 'J档',
                    'skill_percent': 90,
                    'requirement_percent': [0, 5],
                    'description': '优秀'
                },
                {
                    'grade': 'J-档',
                    'skill_percent': 80,
                    'requirement_percent': [10, 20],
                    'description': '良好'
                },
                {
                    'grade': '合格档',
                    'skill_percent': 50,
                    'requirement_percent': [40, 50],
                    'description': '合格'
                },
                {
                    'grade': '不合格档',
                    'skill_percent': 30,
                    'requirement_percent': [20, 40],
                    'description': '不合格'
                },
                {
                    'grade': '差档',
                    'skill_percent': 0,
                    'requirement_percent': [0, 0],
                    'description': '差'
                }
            ]
        }
        
        # 将公式转换为JSON
        formula_json = json.dumps(grade_formula, ensure_ascii=False)
        
        # 检查公式是否已存在
        cursor.execute("SELECT id FROM department_grade_formulas WHERE department = 'AUT'")
        result = cursor.fetchone()
        
        if result:
            cursor.execute("""
            UPDATE department_grade_formulas 
            SET formula = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (formula_json, "AUT部门职级计算公式", result[0]))
            print("更新AUT部门职级计算公式")
        else:
            cursor.execute("""
            INSERT INTO department_grade_formulas 
            (department, formula, description)
            VALUES (?, ?, ?)
            """, ('AUT', formula_json, "AUT部门职级计算公式"))
            print("添加AUT部门职级计算公式")
        
        # 提交所有更改
        conn.commit()
        
        # 5. 验证更改
        # 验证项目分类和权重
        cursor.execute("""
        SELECT category, COUNT(*), SUM(weight)
        FROM department_assessment_items
        WHERE department = 'AUT'
        GROUP BY category
        """)
        
        categories = cursor.fetchall()
        print("\n当前AUT部门考核项目分类统计:")
        for category, count, total_weight in categories:
            print(f"分类: {category}, 项目数: {count}, 总权重: {total_weight:.4f}")
        
        # 验证公式
        cursor.execute("SELECT formula FROM department_grade_formulas WHERE department = 'AUT'")
        formula_row = cursor.fetchone()
        if formula_row:
            formula = json.loads(formula_row[0])
            print("\nAUT部门职级计算公式:")
            print("职级阈值:")
            for threshold in formula['grade_thresholds']:
                req_percent = f"{threshold['requirement_percent'][0]}-{threshold['requirement_percent'][1]}%" if threshold['requirement_percent'][1] > 0 else "N/A"
                print(f"  {threshold['grade']} ({threshold['description']}): 岗位技能系数 {threshold['skill_percent']}%, 制度要求比例 {req_percent}")
        
        print("\n更新完成！")
        return True
        
    except Exception as e:
        # 发生错误时回滚事务
        conn.rollback()
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 关闭数据库连接
        conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    print("开始更新AUT部门评分系统...")
    result = update_aut_scoring_system()
    print(f"更新结果: {'成功' if result else '失败'}")
    print("脚本执行结束") 
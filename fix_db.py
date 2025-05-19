#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复database.py中的语法错误
"""

import re

def fix_database_file():
    # 读取原始文件
    with open('app/models/database.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 查找行2786附近的问题代码，在"WHERE id = ?"后添加缺失的代码
    pattern = r'UPDATE employees \n\s+SET status = \?, department = \?\n\s+WHERE id = \?\n\s+return False'
    replacement = '''UPDATE employees 
                SET status = ?, department = ?
                WHERE id = ?
                """, (status, department, employee_id))
                
                # 更新职级数据
                for year in range(2022, 2026):
                    grade_field = f"{year} Skill Level"
                    if grade_field in row and pd.notna(row[grade_field]):
                        grade = str(row[grade_field])
                        
                        # 添加到职级历史表
                        self.add_employee_grade(
                            employee_id=employee_id,
                            year=year,
                            grade=grade,
                            comment=f"从CSV导入的{year}年职级",
                            user=user
                        )
                        
                        # 同时更新员工表中对应的职级字段
                        grade_column = f"grade_{year}"
                        self.cursor.execute(f"""
                        UPDATE employees SET {grade_column} = ? WHERE id = ?
                        """, (grade, employee_id))
                        
                        count_updated += 1
                
            self.conn.commit()
            
            # 记录操作日志
            self.log_operation(
                user, 
                '导入职级CSV', 
                f"从{file_path}导入职级数据，成功更新{count_updated}条职级记录"
            )
            
            return {
                'success': True,
                'updated': count_updated
            }
        except Exception as e:
            print(f"导入职级CSV失败: {e}")
            return False'''
    
    # 修复代码
    fixed_content = re.sub(pattern, replacement, content)
    
    # 保存修复后的文件
    with open('app/models/database.py', 'w', encoding='utf-8') as file:
        file.write(fixed_content)
    
    print("database.py 文件已修复")

if __name__ == "__main__":
    fix_database_file() 
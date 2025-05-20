import sqlite3
import os
import datetime
import pandas as pd
import numpy as np

class EmployeeDatabase:
    def __init__(self, db_path='employee_db.sqlite'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        """连接到数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"成功连接到数据库: {self.db_path}")
            
            # 确保职级历史表存在
            self._create_grade_history_table()
        except sqlite3.Error as e:
            print(f"数据库连接失败: {e}")
            
    def _create_grade_history_table(self):
        """创建职级历史表（如果不存在）"""
        try:
            self.cursor.execute('''
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
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"创建职级历史表失败: {e}")
            
    def get_db_path(self):
        """获取数据库路径"""
        return self.db_path
        
    def close_connection(self):
        """关闭数据库连接"""
        self.close()
        
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("数据库连接已关闭")
    
    def get_all_employees(self):
        """获取所有员工信息"""
        try:
            self.cursor.execute("SELECT * FROM employees")
            columns = [desc[0] for desc in self.cursor.description]
            employees = []
            for row in self.cursor.fetchall():
                employee = dict(zip(columns, row))
                employees.append(employee)
            return employees
        except sqlite3.Error as e:
            print(f"获取所有员工信息失败: {e}")
            return []
    
    def get_employee_by_id(self, employee_id):
        """通过ID获取员工信息"""
        try:
            self.cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
            columns = [desc[0] for desc in self.cursor.description]
            row = self.cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            print(f"获取员工信息失败: {e}")
            return None
    
    def get_employee_by_no(self, employee_no):
        """通过工号获取员工信息"""
        try:
            self.cursor.execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,))
            columns = [desc[0] for desc in self.cursor.description]
            row = self.cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            print(f"获取员工信息失败: {e}")
            return None
    
    def search_employees(self, search_term):
        """搜索员工信息"""
        try:
            query = """
            SELECT * FROM employees 
            WHERE name LIKE ? OR employee_no LIKE ? OR gid LIKE ? OR department LIKE ?
            """
            search_pattern = f"%{search_term}%"
            self.cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            
            columns = [desc[0] for desc in self.cursor.description]
            employees = []
            for row in self.cursor.fetchall():
                employee = dict(zip(columns, row))
                employees.append(employee)
            return employees
        except sqlite3.Error as e:
            print(f"搜索员工信息失败: {e}")
            return []
    
    def add_employee(self, employee_data, user="系统"):
        """添加新员工"""
        try:
            self.cursor.execute('''
            INSERT INTO employees (
                employee_no, gid, name, status, department,
                grade_2020, grade_2021, grade_2022, grade_2023,
                grade_2024, grade_2025, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                employee_data.get('employee_no', ''),
                employee_data.get('gid', ''),
                employee_data.get('name', ''),
                employee_data.get('status', '在职'),
                employee_data.get('department', ''),
                employee_data.get('grade_2020', ''),
                employee_data.get('grade_2021', ''),
                employee_data.get('grade_2022', ''),
                employee_data.get('grade_2023', ''),
                employee_data.get('grade_2024', ''),
                employee_data.get('grade_2025', ''),
                employee_data.get('notes', '')
            ))
            self.conn.commit()
            
            # 获取新添加员工的ID
            self.cursor.execute("SELECT last_insert_rowid()")
            employee_id = self.cursor.fetchone()[0]
            
            # 构建详细的日志信息
            details = []
            field_names = {
                'employee_no': '工号', 'gid': 'GID', 'name': '姓名', 
                'status': '状态', 'department': '部门',
                'grade_2020': '2020年职级', 'grade_2021': '2021年职级', 
                'grade_2022': '2022年职级', 'grade_2023': '2023年职级', 
                'grade_2024': '2024年职级', 'grade_2025': '2025年职级',
                'notes': '备注'
            }
            
            for key, label in field_names.items():
                value = employee_data.get(key, '')
                if value:  # 只记录非空值
                    details.append(f"{label}: '{value}'")
            
            log_details = f"添加员工: {employee_data.get('name', '')} (ID: {employee_id}), 详细信息: {', '.join(details)}"
            
            # 记录操作日志
            self.log_operation(user, '添加员工', log_details)
            return True
        except sqlite3.Error as e:
            print(f"添加员工失败: {e}")
            return False
    
    def update_employee(self, employee_id, updated_data, user="系统"):
        """更新员工信息"""
        try:
            # 获取更新前的员工信息用于日志记录
            self.cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
            old_data = dict(zip([desc[0] for desc in self.cursor.description], self.cursor.fetchone()))
            if not old_data:
                return False
            
            # 构建SET部分的SQL语句
            set_clauses = []
            values = []
            
            for key, value in updated_data.items():
                if key != 'id':  # 不更新ID字段
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            # 添加WHERE条件的值
            values.append(employee_id)
            
            query = f"UPDATE employees SET {', '.join(set_clauses)} WHERE id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            # 构建详细的日志信息，记录修改的字段和修改前后的值
            changes = []
            for key, new_value in updated_data.items():
                if key in old_data and old_data[key] != new_value:
                    old_value = old_data[key]
                    changes.append(f"{key}: '{old_value}' → '{new_value}'")
            
            change_details = ", ".join(changes)
            log_details = f"更新员工: {old_data['name']} (ID: {employee_id}), 修改内容: {change_details}"
            
            # 记录操作日志
            self.log_operation(user, '更新员工信息', log_details)
            return True
        except sqlite3.Error as e:
            print(f"更新员工信息失败: {e}")
            return False
    
    def delete_employee(self, employee_id, user="系统"):
        """删除员工"""
        try:
            # 先获取员工完整信息，用于日志记录
            self.cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
            result = self.cursor.fetchone()
            
            # 检查是否找到员工数据
            if result is None:
                print(f"未找到ID为{employee_id}的员工")
                return False
                
            # 将查询结果转换为字典
            columns = [desc[0] for desc in self.cursor.description]
            employee_data = dict(zip(columns, result))
            
            # 构建详细的日志信息
            details = []
            field_names = {
                'employee_no': '工号', 'gid': 'GID', 'name': '姓名', 
                'status': '状态', 'department': '部门',
                'grade_2020': '2020年职级', 'grade_2021': '2021年职级', 
                'grade_2022': '2022年职级', 'grade_2023': '2023年职级', 
                'grade_2024': '2024年职级', 'grade_2025': '2025年职级',
                'notes': '备注'
            }
            
            for key, label in field_names.items():
                value = employee_data.get(key, '')
                if value:  # 只记录非空值
                    details.append(f"{label}: '{value}'")
            
            # 执行删除
            self.cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            self.conn.commit()
            
            # 记录操作日志
            log_details = f"删除员工: {employee_data['name']} (ID: {employee_id}), 删除的信息: {', '.join(details)}"
            self.log_operation(user, '删除员工', log_details)
            return True
        except sqlite3.Error as e:
            print(f"删除员工失败: {e}")
            return False
        except Exception as e:
            print(f"删除员工时发生未知错误: {e}")
            return False
    
    def import_from_excel(self, file_path, user="系统"):
        """从Excel文件导入员工数据"""
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                print("不支持的文件格式")
                return False
            
            # 获取现有员工工号列表，用于避免重复导入
            self.cursor.execute("SELECT employee_no FROM employees")
            existing_employee_nos = [row[0] for row in self.cursor.fetchall()]
            
            # 处理导入
            count_added = 0
            count_skipped = 0
            
            for _, row in df.iterrows():
                employee_data = row.to_dict()
                
                # 如果员工工号已存在，则跳过
                if 'employee_no' in employee_data and employee_data['employee_no'] in existing_employee_nos:
                    count_skipped += 1
                    continue
                
                # 添加新员工
                success = self.add_employee(employee_data, user)
                if success:
                    count_added += 1
            
            # 记录操作日志
            self.log_operation(
                user, 
                '导入Excel', 
                f"从{file_path}导入员工数据，成功添加{count_added}条记录，跳过{count_skipped}条记录"
            )
            
            return {
                'success': True,
                'added': count_added,
                'skipped': count_skipped
            }
        except Exception as e:
            print(f"导入Excel失败: {e}")
            return False
    
    def export_to_excel(self, file_path, filters=None):
        """导出员工数据到Excel"""
        try:
            # 根据筛选条件获取员工数据
            if filters:
                # 这里可以根据filters参数构建查询条件
                pass
            else:
                # 如果没有筛选条件，获取所有员工
                employees = self.get_all_employees()
            
            # 转换为DataFrame
            df = pd.DataFrame(employees)
            
            # 导出到Excel
            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            elif file_path.endswith('.csv'):
                df.to_csv(file_path, index=False, encoding='utf-8')
            else:
                # 默认导出为Excel
                file_path = file_path + '.xlsx'
                df.to_excel(file_path, index=False)
            
            return True
        except Exception as e:
            print(f"导出Excel失败: {e}")
            return False
    
    def get_operation_logs(self, limit=100):
        """获取操作日志"""
        try:
            self.cursor.execute(
                "SELECT * FROM operation_logs ORDER BY timestamp DESC LIMIT ?", 
                (limit,)
            )
            columns = [desc[0] for desc in self.cursor.description]
            logs = []
            for row in self.cursor.fetchall():
                log = dict(zip(columns, row))
                logs.append(log)
            return logs
        except sqlite3.Error as e:
            print(f"获取操作日志失败: {e}")
            return []
    
    def log_operation(self, user, operation, details):
        """记录操作日志"""
        try:
            timestamp = datetime.datetime.now()
            self.cursor.execute('''
            INSERT INTO operation_logs (user, operation, details, timestamp)
            VALUES (?, ?, ?, ?)
            ''', (user, operation, details, timestamp))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"记录操作日志失败: {e}")
            return False
    
    def get_statistics(self):
        """获取统计数据"""
        try:
            stats = {}
            
            # 员工总数
            self.cursor.execute("SELECT COUNT(*) FROM employees")
            stats['total_employees'] = self.cursor.fetchone()[0]
            
            # 部门分布
            self.cursor.execute("SELECT department, COUNT(*) FROM employees GROUP BY department")
            stats['department_distribution'] = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            # 职级分布
            grade_years = ['grade_2020', 'grade_2021', 'grade_2022', 'grade_2023', 'grade_2024', 'grade_2025']
            stats['grade_distribution'] = {}
            
            for year in grade_years:
                self.cursor.execute(f"SELECT {year}, COUNT(*) FROM employees WHERE {year} != '' GROUP BY {year}")
                stats['grade_distribution'][year] = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            return stats
        except sqlite3.Error as e:
            print(f"获取统计数据失败: {e}")
            return {}
    
    def backup_database(self, backup_path=None):
        """备份数据库"""
        if not backup_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_{timestamp}.sqlite"
        
        try:
            # 确保连接已关闭
            if self.conn:
                self.conn.close()
            
            # 简单复制文件作为备份
            import shutil
            shutil.copyfile(self.db_path, backup_path)
            
            # 重新连接数据库
            self.connect()
            
            # 记录备份操作
            self.log_operation("系统", "数据库备份", f"数据库已备份到 {backup_path}")
            
            return True, backup_path
        except Exception as e:
            print(f"备份数据库失败: {e}")
            # 尝试重新连接
            self.connect()
            return False, None
    
    def restore_database(self, backup_path, user="系统"):
        """恢复数据库"""
        try:
            # 确保连接已关闭
            if self.conn:
                self.conn.close()
            
            # 导入备份
            import shutil
            shutil.copyfile(backup_path, self.db_path)
            
            # 重新连接数据库
            self.connect()
            
            # 记录恢复操作
            self.log_operation(user, "数据库恢复", f"数据库已从 {backup_path} 恢复")
            
            return True
        except Exception as e:
            print(f"恢复数据库失败: {e}")
            # 尝试重新连接
            self.connect()
            return False
    
    def get_employee_grades(self, employee_id):
        """获取员工的所有职级历史记录"""
        try:
            self.cursor.execute("""
            SELECT * FROM employee_grades 
            WHERE employee_id = ? 
            ORDER BY year DESC
            """, (employee_id,))
            
            columns = [desc[0] for desc in self.cursor.description]
            grades = []
            for row in self.cursor.fetchall():
                grade = dict(zip(columns, row))
                grades.append(grade)
            return grades
        except sqlite3.Error as e:
            print(f"获取员工职级历史失败: {e}")
            return []
    
    def add_employee_grade(self, employee_id, year, grade, comment="", user="系统"):
        """添加或更新员工的特定年份职级"""
        try:
            # 尝试插入新记录，如果已存在则更新
            self.cursor.execute("""
            INSERT INTO employee_grades (employee_id, year, grade, comment)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(employee_id, year) 
            DO UPDATE SET grade = ?, comment = ?, updated_at = CURRENT_TIMESTAMP
            """, (employee_id, year, grade, comment, grade, comment))
            
            self.conn.commit()
            
            # 记录操作日志
            employee_name = self.get_employee_name(employee_id)
            log_details = f"更新员工职级: {employee_name} (ID: {employee_id}), {year}年职级: {grade}"
            if comment:
                log_details += f", 备注: {comment}"
                
            self.log_operation(user, '更新职级信息', log_details)
            return True
        except sqlite3.Error as e:
            print(f"添加/更新员工职级失败: {e}")
            return False
    
    def delete_employee_grade(self, grade_id, user="系统"):
        """删除指定的职级记录"""
        try:
            # 先获取职级记录信息用于日志
            self.cursor.execute("SELECT employee_no, year, grade FROM employee_grades WHERE id = ?", (grade_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return False
                
            employee_no, year, grade = result
            
            # 执行删除
            self.cursor.execute("DELETE FROM employee_grades WHERE id = ?", (grade_id,))
            
            # 同时清空employees表中对应年份的职级字段
            grade_field = f"grade_{year}"
            self.cursor.execute(f"""
            UPDATE employees 
            SET {grade_field} = '' 
            WHERE employee_no = ?
            """, (employee_no,))
            
            self.conn.commit()
            
            # 记录操作日志
            employee_name = self._get_employee_name(employee_no)
            log_details = f"删除员工职级记录: {employee_name} (工号: {employee_no}), {year}年职级: {grade}"
            self.log_operation(user, '删除职级记录', log_details)
            
            return True
        except sqlite3.Error as e:
            print(f"删除员工职级记录失败: {e}")
            return False
    
    def get_employee_name(self, employee_id):
        """获取员工姓名"""
        try:
            self.cursor.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "未知员工"
        except sqlite3.Error as e:
            print(f"获取员工姓名失败: {e}")
            return "未知员工"
            
    def migrate_existing_grades(self):
        """将现有表中的职级数据迁移到新的职级历史表中"""
        try:
            # 获取所有员工
            employees = self.get_all_employees()
            migrated_count = 0
            
            for employee in employees:
                employee_id = employee['id']
                
                # 检查现有的年份职级数据
                years = [2020, 2021, 2022, 2023, 2024, 2025]
                for year in years:
                    grade_field = f"grade_{year}"
                    if grade_field in employee and employee[grade_field]:
                        # 添加到新表中
                        self.add_employee_grade(
                            employee_id=employee_id,
                            year=year,
                            grade=employee[grade_field],
                            comment="从旧数据迁移",
                            user="系统"
                        )
                        migrated_count += 1
            
            return migrated_count
        except Exception as e:
            print(f"迁移职级数据失败: {e}")
            return 0 
    
    def update_employee_by_no(self, employee_no, updated_data, user="系统"):
        """通过员工工号更新员工信息"""
        try:
            # 获取更新前的员工信息用于日志记录
            self.cursor.execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,))
            old_data = dict(zip([desc[0] for desc in self.cursor.description], self.cursor.fetchone()))
            if not old_data:
                return False
            
            # 构建SET部分的SQL语句
            set_clauses = []
            values = []
            
            for key, value in updated_data.items():
                if key != 'employee_no':  # 不更新工号字段
                    # 确保值不为None，如果是None则转换为空字符串
                    if value is None:
                        value = ""
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            # 添加WHERE条件的值
            values.append(employee_no)
            
            query = f"UPDATE employees SET {', '.join(set_clauses)} WHERE employee_no = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            # 构建详细的日志信息，记录修改的字段和修改前后的值
            changes = []
            for key, new_value in updated_data.items():
                if key in old_data and old_data[key] != new_value:
                    old_value = old_data[key]
                    changes.append(f"{key}: '{old_value}' → '{new_value}'")
            
            change_details = ", ".join(changes)
            log_details = f"更新员工: {old_data['name']} (工号: {employee_no}), 修改内容: {change_details}"
            
            # 记录操作日志
            self.log_operation(user, '更新员工信息', log_details)
            return True
        except sqlite3.Error as e:
            print(f"更新员工信息失败: {e}")
            return False
    
    def delete_employee_by_no(self, employee_no, user="系统"):
        """通过员工工号删除员工"""
        try:
            # 先获取员工完整信息，用于日志记录
            self.cursor.execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,))
            result = self.cursor.fetchone()
            
            # 检查是否找到员工数据
            if result is None:
                print(f"未找到工号为{employee_no}的员工")
                return False
                
            # 将查询结果转换为字典
            columns = [desc[0] for desc in self.cursor.description]
            employee_data = dict(zip(columns, result))
            
            # 构建详细的日志信息
            details = []
            field_names = {
                'employee_no': '工号', 'gid': 'GID', 'name': '姓名', 
                'status': '状态', 'department': '部门',
                'grade_2020': '2020年职级', 'grade_2021': '2021年职级', 
                'grade_2022': '2022年职级', 'grade_2023': '2023年职级', 
                'grade_2024': '2024年职级', 'grade_2025': '2025年职级',
                'notes': '备注'
            }
            
            for key, label in field_names.items():
                value = employee_data.get(key, '')
                if value:  # 只记录非空值
                    details.append(f"{label}: '{value}'")
            
            # 执行删除
            self.cursor.execute("DELETE FROM employees WHERE employee_no = ?", (employee_no,))
            self.conn.commit()
            
            # 记录操作日志
            log_details = f"删除员工: {employee_data['name']} (工号: {employee_no}), 删除的信息: {', '.join(details)}"
            self.log_operation(user, '删除员工', log_details)
            return True
        except sqlite3.Error as e:
            print(f"删除员工失败: {e}")
            return False
        except Exception as e:
            print(f"删除员工时发生未知错误: {e}")
            return False
    
    def get_employee_grades_by_no(self, employee_no):
        """通过员工工号获取所有职级历史记录"""
        try:
            self.cursor.execute("""
            SELECT * FROM employee_grades 
            WHERE employee_no = ? 
            ORDER BY year DESC
            """, (employee_no,))
            
            columns = [desc[0] for desc in self.cursor.description]
            grades = []
            for row in self.cursor.fetchall():
                grade = dict(zip(columns, row))
                grades.append(grade)
            return grades
        except sqlite3.Error as e:
            print(f"通过工号获取员工职级历史失败: {e}")
            return []
    
    def add_employee_grade_by_no(self, employee_no, year, grade, comment="", user="系统"):
        """通过员工工号添加或更新职级记录"""
        try:
            # 尝试插入新记录，如果已存在则更新
            self.cursor.execute("""
            INSERT INTO employee_grades (employee_no, year, grade, comment)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(employee_no, year) 
            DO UPDATE SET grade = ?, comment = ?, updated_at = CURRENT_TIMESTAMP
            """, (employee_no, year, grade, comment, grade, comment))
            
            # 同时更新employees表中对应年份的职级字段
            grade_field = f"grade_{year}"
            self.cursor.execute(f"""
            UPDATE employees 
            SET {grade_field} = ? 
            WHERE employee_no = ?
            """, (grade, employee_no))
            
            self.conn.commit()
            
            # 记录操作日志
            employee_name = self._get_employee_name(employee_no)
            log_details = f"更新员工职级: {employee_name} (工号: {employee_no}), {year}年职级: {grade}"
            if comment:
                log_details += f", 备注: {comment}"
                
            self.log_operation(user, '更新职级信息', log_details)
            return True
        except sqlite3.Error as e:
            print(f"通过工号添加员工职级历史失败: {e}")
            return False
            
    def _get_employee_name(self, employee_no):
        """通过工号获取员工姓名"""
        try:
            self.cursor.execute("SELECT name FROM employees WHERE employee_no = ?", (employee_no,))
            result = self.cursor.fetchone()
            return result[0] if result else "未知员工"
        except sqlite3.Error as e:
            print(f"获取员工姓名失败: {e}")
            return "未知员工" 
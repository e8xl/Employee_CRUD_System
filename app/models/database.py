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
        except sqlite3.Error as e:
            print(f"数据库连接失败: {e}")
            
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
            
            # 记录操作日志
            self.log_operation(user, '添加员工', f"添加员工: {employee_data.get('name', '')}")
            return True
        except sqlite3.Error as e:
            print(f"添加员工失败: {e}")
            return False
    
    def update_employee(self, employee_id, updated_data, user="系统"):
        """更新员工信息"""
        try:
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
            
            # 记录操作日志
            self.log_operation(user, '更新员工信息', f"更新员工ID: {employee_id}")
            return True
        except sqlite3.Error as e:
            print(f"更新员工信息失败: {e}")
            return False
    
    def delete_employee(self, employee_id, user="系统"):
        """删除员工"""
        try:
            # 先获取员工信息，用于日志记录
            self.cursor.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
            result = self.cursor.fetchone()
            if result:
                employee_name = result[0]
                # 执行删除
                self.cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
                self.conn.commit()
                # 记录操作日志
                self.log_operation(user, '删除员工', f"删除员工: {employee_name} (ID: {employee_id})")
                return True
            return False
        except sqlite3.Error as e:
            print(f"删除员工失败: {e}")
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
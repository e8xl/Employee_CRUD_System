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
            # 确保技能评分相关表存在
            self._create_skill_tables()
        except sqlite3.Error as e:
            print(f"数据库连接失败: {e}")
            
    def _create_grade_history_table(self):
        """创建职级历史表（如果不存在）"""
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                grade TEXT NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                UNIQUE(employee_id, year)
            )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"创建职级历史表失败: {e}")
    
    def _create_skill_tables(self):
        """创建技能评分相关表（如果不存在）"""
        try:
            # 技能评分总表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                basic_knowledge_score REAL DEFAULT 0,  -- 基础知识分数
                position_skill_score REAL DEFAULT 0,   -- 岗位技能分数
                cross_department_score REAL DEFAULT 0, -- 跨部门技能分数
                technician_skill_score REAL DEFAULT 0, -- 技师技能分数
                management_skill_score REAL DEFAULT 0, -- 一线管理技能分数
                total_score REAL DEFAULT 0,            -- 总分
                evaluated_grade TEXT,                  -- 评定的职级
                comment TEXT,                          -- 备注
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                UNIQUE(employee_id, year)
            )
            ''')
            
            # 技能明细评分表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_detail_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_score_id INTEGER NOT NULL,
                skill_code TEXT NOT NULL,              -- 技能代码，如RUB, USB等
                skill_name TEXT,                       -- 技能名称
                skill_type TEXT,                       -- 技能类型(基础知识/岗位技能/跨部门技能/技师技能/一线管理技能)
                skill_score INTEGER,                   -- 评分(0-4)
                FOREIGN KEY (skill_score_id) REFERENCES skill_scores(id) ON DELETE CASCADE
            )
            ''')
            
            # 职级评定阈值表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_thresholds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                grade TEXT NOT NULL,                   -- 职级(G1, G2, G3, G4A, G4B)
                basic_knowledge_min REAL,              -- 基础知识最低分
                position_skill_min REAL,               -- 岗位技能最低分
                cross_department_min REAL,             -- 跨部门技能最低分
                technician_skill_min REAL,             -- 技师技能最低分
                management_skill_min REAL,             -- 一线管理技能最低分
                total_min REAL,                        -- 总分最低要求
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, grade)
            )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"创建技能评分相关表失败: {e}")
            
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
            
    def get_employee_skill_scores(self, employee_id, year=None):
        """获取员工的技能评分"""
        try:
            if year:
                self.cursor.execute("""
                SELECT * FROM skill_scores 
                WHERE employee_id = ? AND year = ?
                """, (employee_id, year))
            else:
                self.cursor.execute("""
                SELECT * FROM skill_scores 
                WHERE employee_id = ? 
                ORDER BY year DESC
                """, (employee_id,))
            
            columns = [desc[0] for desc in self.cursor.description]
            scores = []
            for row in self.cursor.fetchall():
                score = dict(zip(columns, row))
                scores.append(score)
            return scores
        except sqlite3.Error as e:
            print(f"获取员工技能评分失败: {e}")
            return []
    
    def get_employee_skill_details(self, skill_score_id):
        """获取技能评分的详细数据"""
        try:
            self.cursor.execute("""
            SELECT * FROM skill_detail_scores 
            WHERE skill_score_id = ?
            """, (skill_score_id,))
            
            columns = [desc[0] for desc in self.cursor.description]
            details = []
            for row in self.cursor.fetchall():
                detail = dict(zip(columns, row))
                details.append(detail)
            return details
        except sqlite3.Error as e:
            print(f"获取技能评分详情失败: {e}")
            return []
            
    def get_skill_statistics(self, year=None):
        """获取技能评分统计数据"""
        try:
            stats = {}
            
            # 如果未指定年份，获取最新的年份
            if year is None:
                self.cursor.execute("SELECT MAX(year) FROM skill_scores")
                result = self.cursor.fetchone()
                year = result[0] if result and result[0] else datetime.datetime.now().year
            
            # 获取各职级的员工数量
            self.cursor.execute("""
            SELECT evaluated_grade, COUNT(*) FROM skill_scores
            WHERE year = ? GROUP BY evaluated_grade
            """, (year,))
            
            stats['grade_distribution'] = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            # 获取各技能分数段的分布
            skill_fields = [
                ('basic_knowledge_score', '基础知识'),
                ('position_skill_score', '岗位技能'),
                ('cross_department_score', '跨部门技能'),
                ('technician_skill_score', '技师技能'),
                ('management_skill_score', '一线管理技能')
            ]
            
            stats['skill_distributions'] = {}
            
            for field, label in skill_fields:
                self.cursor.execute(f"""
                SELECT 
                    CASE 
                        WHEN {field} < 20 THEN '0-20'
                        WHEN {field} < 40 THEN '20-40'
                        WHEN {field} < 60 THEN '40-60'
                        WHEN {field} < 80 THEN '60-80'
                        ELSE '80-100'
                    END as score_range,
                    COUNT(*) as count
                FROM skill_scores
                WHERE year = ?
                GROUP BY score_range
                """, (year,))
                
                stats['skill_distributions'][label] = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            return stats
        except sqlite3.Error as e:
            print(f"获取技能评分统计数据失败: {e}")
            return {}
    
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
            
    def import_skill_scores(self, file_path, year, user="系统"):
        """导入技能评分数据 - 简化实现"""
        print(f"导入技能评分数据: {file_path}")
        self.log_operation(user, '导入技能评分', f"从{file_path}导入{year}年技能评分数据")
        return {'success': True, 'added': 0}
        
    def import_skill_thresholds(self, file_path, year, user="系统"):
        """导入职级阈值数据 - 简化实现"""
        print(f"导入职级阈值数据: {file_path}")
        self.log_operation(user, '导入职级阈值', f"从{file_path}导入{year}年职级评定阈值")
        return {'success': True, 'added': 0}
        
    def apply_evaluated_grades(self, year, target_year, user="系统"):
        """将评定的职级应用到员工表中 - 简化实现"""
        print(f"应用{year}年职级到{target_year}年")
        self.log_operation(user, '应用评定职级', f"将{year}年技能评分评定的职级应用到{target_year}年")
        return 0
        
    def export_evaluation_results(self, year, file_path, user="系统"):
        """导出职级评定结果 - 简化实现"""
        print(f"导出评定结果到: {file_path}")
        self.log_operation(user, '导出评定结果', f"导出{year}年职级评定结果到{file_path}")
        return True 
import sqlite3
import os
import datetime
import json
import pandas as pd
import numpy as np

class ScoreDatabase:
    """成绩管理系统数据库类"""
    
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
            
            # 确保所有表都存在
            self._create_tables()
        except sqlite3.Error as e:
            print(f"数据库连接失败: {e}")
    
    def _create_tables(self):
        """创建所有所需表（如果不存在）"""
        self._create_department_assessment_items_table()
        self._create_department_grade_formulas_table()
        self._create_employee_scores_table()
        self._create_predicted_grades_table()
        
    def _create_department_assessment_items_table(self):
        """创建部门考核项目表"""
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS department_assessment_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT NOT NULL,
                assessment_name TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                max_score REAL DEFAULT 100.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(department, assessment_name)
            )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"创建部门考核项目表失败: {e}")
            
    def _create_department_grade_formulas_table(self):
        """创建部门职级计算公式表"""
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS department_grade_formulas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT NOT NULL UNIQUE,
                formula TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"创建部门职级计算公式表失败: {e}")
            
    def _create_employee_scores_table(self):
        """创建员工考核成绩表"""
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_no TEXT NOT NULL,
                assessment_year INTEGER NOT NULL,
                assessment_item_id INTEGER NOT NULL,
                score REAL NOT NULL,
                comment TEXT,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assessment_item_id) REFERENCES department_assessment_items(id) ON DELETE CASCADE,
                UNIQUE(employee_no, assessment_year, assessment_item_id)
            )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"创建员工考核成绩表失败: {e}")
            
    def _create_predicted_grades_table(self):
        """创建预测职级表"""
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS predicted_grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_no TEXT NOT NULL,
                assessment_year INTEGER NOT NULL,
                current_grade TEXT NOT NULL,
                predicted_grade TEXT NOT NULL,
                total_score REAL NOT NULL,
                calculation_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(employee_no, assessment_year)
            )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"创建预测职级表失败: {e}")
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("数据库连接已关闭")
    
    # 部门考核项目管理方法
    def get_all_assessment_items(self, department=None):
        """获取所有考核项目，可按部门筛选"""
        try:
            if department:
                self.cursor.execute(
                    "SELECT * FROM department_assessment_items WHERE department = ? ORDER BY department, assessment_name",
                    (department,)
                )
            else:
                self.cursor.execute(
                    "SELECT * FROM department_assessment_items ORDER BY department, assessment_name"
                )
            
            columns = [desc[0] for desc in self.cursor.description]
            items = []
            for row in self.cursor.fetchall():
                item = dict(zip(columns, row))
                items.append(item)
            return items
        except sqlite3.Error as e:
            print(f"获取考核项目失败: {e}")
            return []
    
    def add_assessment_item(self, item_data, user="系统"):
        """添加考核项目"""
        try:
            self.cursor.execute('''
            INSERT INTO department_assessment_items (
                department, assessment_name, weight, max_score
            ) VALUES (?, ?, ?, ?)
            ''', (
                item_data.get('department', ''),
                item_data.get('assessment_name', ''),
                item_data.get('weight', 1.0),
                item_data.get('max_score', 100.0)
            ))
            self.conn.commit()
            
            # 获取新添加项目的ID
            self.cursor.execute("SELECT last_insert_rowid()")
            item_id = self.cursor.fetchone()[0]
            
            # 记录操作日志
            self._log_operation(
                user, 
                '添加考核项目', 
                f"添加考核项目: {item_data.get('assessment_name')} 到部门 {item_data.get('department')}"
            )
            return item_id
        except sqlite3.Error as e:
            print(f"添加考核项目失败: {e}")
            return None
    
    def update_assessment_item(self, item_id, item_data, user="系统"):
        """更新考核项目"""
        try:
            # 获取更新前的信息用于日志
            self.cursor.execute("SELECT * FROM department_assessment_items WHERE id = ?", (item_id,))
            old_data = dict(zip([desc[0] for desc in self.cursor.description], self.cursor.fetchone()))
            
            self.cursor.execute('''
            UPDATE department_assessment_items SET 
                department = ?, 
                assessment_name = ?, 
                weight = ?, 
                max_score = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (
                item_data.get('department', old_data['department']),
                item_data.get('assessment_name', old_data['assessment_name']),
                item_data.get('weight', old_data['weight']),
                item_data.get('max_score', old_data['max_score']),
                item_id
            ))
            self.conn.commit()
            
            # 记录操作日志
            changes = []
            for key in ['department', 'assessment_name', 'weight', 'max_score']:
                if key in item_data and item_data[key] != old_data[key]:
                    changes.append(f"{key}: '{old_data[key]}' → '{item_data[key]}'")
            
            self._log_operation(
                user, 
                '更新考核项目', 
                f"更新考核项目 ID: {item_id}, {', '.join(changes)}"
            )
            return True
        except sqlite3.Error as e:
            print(f"更新考核项目失败: {e}")
            return False
    
    def delete_assessment_item(self, item_id, user="系统"):
        """删除考核项目"""
        try:
            # 获取要删除的项目信息用于日志
            self.cursor.execute("SELECT * FROM department_assessment_items WHERE id = ?", (item_id,))
            item_data = dict(zip([desc[0] for desc in self.cursor.description], self.cursor.fetchone()))
            
            # 执行删除
            self.cursor.execute("DELETE FROM department_assessment_items WHERE id = ?", (item_id,))
            self.conn.commit()
            
            # 记录操作日志
            self._log_operation(
                user, 
                '删除考核项目', 
                f"删除考核项目: {item_data['assessment_name']} (ID: {item_id}) 从部门 {item_data['department']}"
            )
            return True
        except sqlite3.Error as e:
            print(f"删除考核项目失败: {e}")
            return False
    
    def import_assessment_items(self, file_path, user="系统"):
        """从Excel/CSV导入考核项目"""
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                print("不支持的文件格式")
                return False
            
            required_columns = ['department', 'assessment_name']
            for col in required_columns:
                if col not in df.columns:
                    print(f"导入文件缺少必要列: {col}")
                    return False
            
            count_added = 0
            count_updated = 0
            
            for _, row in df.iterrows():
                item_data = {
                    'department': row['department'],
                    'assessment_name': row['assessment_name'],
                    'weight': row.get('weight', 1.0),
                    'max_score': row.get('max_score', 100.0)
                }
                
                # 检查是否已存在
                self.cursor.execute(
                    "SELECT id FROM department_assessment_items WHERE department = ? AND assessment_name = ?",
                    (item_data['department'], item_data['assessment_name'])
                )
                
                result = self.cursor.fetchone()
                if result:
                    # 更新已存在的项目
                    item_id = result[0]
                    if self.update_assessment_item(item_id, item_data, user):
                        count_updated += 1
                else:
                    # 添加新项目
                    if self.add_assessment_item(item_data, user):
                        count_added += 1
            
            # 记录操作日志
            self._log_operation(
                user, 
                '导入考核项目', 
                f"从{file_path}导入考核项目，添加{count_added}项，更新{count_updated}项"
            )
            
            return {
                'success': True,
                'added': count_added,
                'updated': count_updated
            }
        except Exception as e:
            print(f"导入考核项目失败: {e}")
            return False
    
    # 部门职级计算公式管理方法
    def get_department_formula(self, department):
        """获取部门职级计算公式"""
        try:
            self.cursor.execute(
                "SELECT * FROM department_grade_formulas WHERE department = ?",
                (department,)
            )
            result = self.cursor.fetchone()
            if result:
                columns = [desc[0] for desc in self.cursor.description]
                formula_data = dict(zip(columns, result))
                # 将JSON字符串转换为字典
                formula_data['formula'] = json.loads(formula_data['formula'])
                return formula_data
            return None
        except sqlite3.Error as e:
            print(f"获取部门公式失败: {e}")
            return None
    
    def save_department_formula(self, department, formula, description="", user="系统"):
        """保存部门职级计算公式"""
        try:
            # 将公式转换为JSON字符串
            formula_json = json.dumps(formula)
            
            # 检查是否已存在该部门的公式
            self.cursor.execute(
                "SELECT id FROM department_grade_formulas WHERE department = ?",
                (department,)
            )
            result = self.cursor.fetchone()
            
            if result:
                # 更新现有公式
                self.cursor.execute('''
                UPDATE department_grade_formulas SET 
                    formula = ?, 
                    description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE department = ?
                ''', (formula_json, description, department))
                operation_type = '更新部门公式'
            else:
                # 添加新公式
                self.cursor.execute('''
                INSERT INTO department_grade_formulas (
                    department, formula, description
                ) VALUES (?, ?, ?)
                ''', (department, formula_json, description))
                operation_type = '添加部门公式'
            
            self.conn.commit()
            
            # 记录操作日志
            self._log_operation(
                user, 
                operation_type, 
                f"{operation_type}: {department}, 描述: {description}"
            )
            return True
        except sqlite3.Error as e:
            print(f"保存部门公式失败: {e}")
            return False
    
    def get_all_department_formulas(self):
        """获取所有部门的职级计算公式"""
        try:
            self.cursor.execute("SELECT * FROM department_grade_formulas ORDER BY department")
            
            columns = [desc[0] for desc in self.cursor.description]
            formulas = []
            for row in self.cursor.fetchall():
                formula_data = dict(zip(columns, row))
                # 将JSON字符串转换为字典
                formula_data['formula'] = json.loads(formula_data['formula'])
                formulas.append(formula_data)
            return formulas
        except sqlite3.Error as e:
            print(f"获取所有部门公式失败: {e}")
            return []
    
    # 员工成绩管理方法
    def get_employee_scores(self, employee_no, assessment_year=None):
        """获取员工的考核成绩"""
        try:
            if assessment_year:
                self.cursor.execute('''
                SELECT s.*, a.assessment_name, a.department, a.weight, a.max_score
                FROM employee_scores s
                JOIN department_assessment_items a ON s.assessment_item_id = a.id
                WHERE s.employee_no = ? AND s.assessment_year = ?
                ORDER BY a.department, a.assessment_name
                ''', (employee_no, assessment_year))
            else:
                self.cursor.execute('''
                SELECT s.*, a.assessment_name, a.department, a.weight, a.max_score
                FROM employee_scores s
                JOIN department_assessment_items a ON s.assessment_item_id = a.id
                WHERE s.employee_no = ?
                ORDER BY s.assessment_year DESC, a.department, a.assessment_name
                ''', (employee_no,))
            
            columns = [desc[0] for desc in self.cursor.description]
            scores = []
            for row in self.cursor.fetchall():
                score = dict(zip(columns, row))
                scores.append(score)
            return scores
        except sqlite3.Error as e:
            print(f"获取员工成绩失败: {e}")
            return []
    
    def get_department_employee_scores(self, department, assessment_year):
        """获取部门所有员工的某年度考核成绩"""
        try:
            self.cursor.execute('''
            SELECT s.*, e.name as employee_name, e.employee_no, 
                   a.assessment_name, a.weight, a.max_score
            FROM employee_scores s
            JOIN employees e ON s.employee_no = e.employee_no
            JOIN department_assessment_items a ON s.assessment_item_id = a.id
            WHERE e.department = ? AND s.assessment_year = ?
            ORDER BY e.name, a.assessment_name
            ''', (department, assessment_year))
            
            columns = [desc[0] for desc in self.cursor.description]
            scores = []
            for row in self.cursor.fetchall():
                score = dict(zip(columns, row))
                scores.append(score)
            return scores
        except sqlite3.Error as e:
            print(f"获取部门员工成绩失败: {e}")
            return []
    
    def save_employee_score(self, score_data, user="系统"):
        """保存员工考核成绩"""
        try:
            # 检查是否已存在该成绩记录
            self.cursor.execute('''
            SELECT id FROM employee_scores 
            WHERE employee_no = ? AND assessment_year = ? AND assessment_item_id = ?
            ''', (
                score_data.get('employee_no'),
                score_data.get('assessment_year'),
                score_data.get('assessment_item_id')
            ))
            result = self.cursor.fetchone()
            
            if result:
                # 更新现有成绩
                self.cursor.execute('''
                UPDATE employee_scores SET 
                    score = ?, 
                    comment = ?,
                    created_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (
                    score_data.get('score'),
                    score_data.get('comment', ''),
                    user,
                    result[0]
                ))
                operation_type = '更新员工成绩'
            else:
                # 添加新成绩
                self.cursor.execute('''
                INSERT INTO employee_scores (
                    employee_no, assessment_year, assessment_item_id, 
                    score, comment, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    score_data.get('employee_no'),
                    score_data.get('assessment_year'),
                    score_data.get('assessment_item_id'),
                    score_data.get('score'),
                    score_data.get('comment', ''),
                    user
                ))
                operation_type = '添加员工成绩'
            
            self.conn.commit()
            
            # 获取员工姓名和考核项目名称
            employee_name = self._get_employee_name(score_data.get('employee_no'))
            item_name = self._get_assessment_item_name(score_data.get('assessment_item_id'))
            
            # 记录操作日志
            self._log_operation(
                user, 
                operation_type, 
                f"{operation_type}: {employee_name}, {score_data.get('assessment_year')}年, 项目: {item_name}, 分数: {score_data.get('score')}"
            )
            return True
        except sqlite3.Error as e:
            print(f"保存员工成绩失败: {e}")
            return False
    
    def import_employee_scores(self, file_path, assessment_year, user="系统"):
        """从Excel/CSV导入员工成绩"""
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                print("不支持的文件格式")
                return False
            
            required_columns = ['employee_no', 'assessment_name', 'score']
            for col in required_columns:
                if col not in df.columns:
                    print(f"导入文件缺少必要列: {col}")
                    return False
            
            count_added = 0
            count_updated = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # 获取员工部门
                    employee_no = str(row['employee_no']).strip()
                    self.cursor.execute("SELECT department FROM employees WHERE employee_no = ?", (employee_no,))
                    department_result = self.cursor.fetchone()
                    if not department_result:
                        errors.append(f"找不到工号为 {employee_no} 的员工")
                        continue
                    department = department_result[0]
                    
                    # 获取考核项目ID
                    assessment_name = str(row['assessment_name']).strip()
                    
                    self.cursor.execute(
                        "SELECT id FROM department_assessment_items WHERE department = ? AND assessment_name = ?",
                        (department, assessment_name)
                    )
                    item_result = self.cursor.fetchone()
                    if not item_result:
                        errors.append(f"找不到部门 {department} 的考核项目: {assessment_name}")
                        continue
                    assessment_item_id = item_result[0]
                    
                    # 准备成绩数据
                    score_data = {
                        'employee_no': employee_no,
                        'assessment_year': assessment_year,
                        'assessment_item_id': assessment_item_id,
                        'score': float(row['score']),
                        'comment': row.get('comment', '')
                    }
                    
                    # 检查是否已存在该成绩记录
                    self.cursor.execute('''
                    SELECT id FROM employee_scores 
                    WHERE employee_no = ? AND assessment_year = ? AND assessment_item_id = ?
                    ''', (
                        score_data['employee_no'],
                        score_data['assessment_year'],
                        score_data['assessment_item_id']
                    ))
                    result = self.cursor.fetchone()
                    
                    if result:
                        # 更新现有成绩
                        self.cursor.execute('''
                        UPDATE employee_scores SET 
                            score = ?, 
                            comment = ?,
                            created_by = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        ''', (
                            score_data['score'],
                            score_data['comment'],
                            user,
                            result[0]
                        ))
                        count_updated += 1
                    else:
                        # 添加新成绩
                        self.cursor.execute('''
                        INSERT INTO employee_scores (
                            employee_no, assessment_year, assessment_item_id, 
                            score, comment, created_by
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            score_data['employee_no'],
                            score_data['assessment_year'],
                            score_data['assessment_item_id'],
                            score_data['score'],
                            score_data['comment'],
                            user
                        ))
                        count_added += 1
                
                except Exception as e:
                    errors.append(f"处理行 {row.name + 1} 时出错: {str(e)}")
            
            self.conn.commit()
            
            # 记录操作日志
            self._log_operation(
                user, 
                '导入员工成绩', 
                f"从{file_path}导入{assessment_year}年员工成绩，添加{count_added}条，更新{count_updated}条，错误{len(errors)}条"
            )
            
            return {
                'success': True,
                'added': count_added,
                'updated': count_updated,
                'errors': errors
            }
        except Exception as e:
            print(f"导入员工成绩失败: {e}")
            return False
    
    # 职级预测方法
    def calculate_predicted_grade(self, employee_no, assessment_year, user="系统"):
        """计算员工预测职级"""
        try:
            # 获取员工信息
            self.cursor.execute(
                "SELECT employee_no, name, department, grade_2023, grade_2024 FROM employees WHERE employee_no = ?", 
                (employee_no,)
            )
            employee = self.cursor.fetchone()
            if not employee:
                print(f"找不到工号为 {employee_no} 的员工")
                return False
            
            employee_no, employee_name, department, grade_2023, grade_2024 = employee
            
            # 确定当前职级
            current_grade = grade_2024 if grade_2024 else grade_2023
            if not current_grade:
                print(f"员工 {employee_name} 没有当前职级信息")
                return False
            
            # 获取部门公式
            formula_data = self.get_department_formula(department)
            if not formula_data:
                print(f"部门 {department} 没有设置职级计算公式")
                return False
            
            formula = formula_data['formula']
            
            # 获取员工所有考核项目成绩
            scores = self.get_employee_scores(employee_no, assessment_year)
            if not scores:
                print(f"员工 {employee_name} 没有 {assessment_year} 年的考核成绩")
                return False
            
            # 计算总分
            total_score = 0
            calculation_details = {
                'scores': [],
                'total': 0,
                'formula': formula_data['description'],
                'predicted_grade': ''
            }
            
            for score in scores:
                weighted_score = score['score'] * score['weight']
                total_score += weighted_score
                
                calculation_details['scores'].append({
                    'item': score['assessment_name'],
                    'raw_score': score['score'],
                    'weight': score['weight'],
                    'weighted_score': weighted_score
                })
            
            calculation_details['total'] = total_score
            
            # 根据公式计算预测职级
            predicted_grade = self._apply_formula(total_score, current_grade, formula)
            calculation_details['predicted_grade'] = predicted_grade
            
            # 保存预测结果
            self.cursor.execute('''
            INSERT OR REPLACE INTO predicted_grades (
                employee_no, assessment_year, current_grade, 
                predicted_grade, total_score, calculation_details
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                employee_no,
                assessment_year,
                current_grade,
                predicted_grade,
                total_score,
                json.dumps(calculation_details)
            ))
            self.conn.commit()
            
            # 记录操作日志
            self._log_operation(
                user, 
                '计算预测职级', 
                f"计算员工 {employee_name} {assessment_year}年预测职级: 从 {current_grade} 到 {predicted_grade}"
            )
            
            return {
                'success': True,
                'employee_no': employee_no,
                'employee_name': employee_name,
                'current_grade': current_grade,
                'predicted_grade': predicted_grade,
                'total_score': total_score,
                'calculation_details': calculation_details
            }
        except Exception as e:
            print(f"计算预测职级失败: {e}")
            return False
    
    def get_predicted_grade(self, employee_no, assessment_year):
        """获取员工的预测职级"""
        try:
            self.cursor.execute('''
            SELECT * FROM predicted_grades
            WHERE employee_no = ? AND assessment_year = ?
            ''', (employee_no, assessment_year))
            
            result = self.cursor.fetchone()
            if result:
                columns = [desc[0] for desc in self.cursor.description]
                grade_data = dict(zip(columns, result))
                # 将JSON字符串转换为字典
                grade_data['calculation_details'] = json.loads(grade_data['calculation_details'])
                return grade_data
            return None
        except sqlite3.Error as e:
            print(f"获取预测职级失败: {e}")
            return None
    
    def get_department_predicted_grades(self, department, assessment_year):
        """获取部门所有员工的预测职级"""
        try:
            self.cursor.execute('''
            SELECT p.*, e.name as employee_name, e.employee_no, e.department
            FROM predicted_grades p
            JOIN employees e ON p.employee_no = e.employee_no
            WHERE e.department = ? AND p.assessment_year = ?
            ORDER BY e.name
            ''', (department, assessment_year))
            
            columns = [desc[0] for desc in self.cursor.description]
            grades = []
            for row in self.cursor.fetchall():
                grade_data = dict(zip(columns, row))
                # 将JSON字符串转换为字典
                grade_data['calculation_details'] = json.loads(grade_data['calculation_details'])
                grades.append(grade_data)
            return grades
        except sqlite3.Error as e:
            print(f"获取部门预测职级失败: {e}")
            return []
    
    # 辅助方法
    def _apply_formula(self, total_score, current_grade, formula):
        """应用职级计算公式计算预测职级"""
        # 示例简单公式，实际项目中可能需要更复杂的实现
        if 'grade_thresholds' in formula:
            thresholds = formula['grade_thresholds']
            for threshold in thresholds:
                if total_score >= threshold['min_score'] and total_score <= threshold['max_score']:
                    return threshold['grade']
        
        # 如果没有匹配的阈值，返回当前职级
        return current_grade
    
    def _get_employee_name(self, employee_no):
        """获取员工姓名"""
        try:
            self.cursor.execute("SELECT name FROM employees WHERE employee_no = ?", (employee_no,))
            result = self.cursor.fetchone()
            return result[0] if result else "未知员工"
        except sqlite3.Error:
            return "未知员工"
    
    def _get_assessment_item_name(self, item_id):
        """获取考核项目名称"""
        try:
            self.cursor.execute("SELECT assessment_name FROM department_assessment_items WHERE id = ?", (item_id,))
            result = self.cursor.fetchone()
            return result[0] if result else "未知项目"
        except sqlite3.Error:
            return "未知项目"
    
    def _log_operation(self, user, operation, details):
        """记录操作日志"""
        try:
            timestamp = datetime.datetime.now()
            self.cursor.execute('''
            INSERT INTO operation_logs (user, operation, details)
            VALUES (?, ?, ?)
            ''', (user, operation, details))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"记录操作日志失败: {e}")
            return False
    
    def get_all_departments(self):
        """获取系统中所有部门"""
        try:
            self.cursor.execute("SELECT DISTINCT department FROM employees WHERE department != '' ORDER BY department")
            departments = [row[0] for row in self.cursor.fetchall()]
            return departments
        except sqlite3.Error as e:
            print(f"获取部门列表失败: {e}")
            return []
    
    def get_department_employees(self, department):
        """获取指定部门的所有员工"""
        try:
            self.cursor.execute(
                "SELECT * FROM employees WHERE department = ? AND status = 'Active' ORDER BY name",
                (department,)
            )
            columns = [desc[0] for desc in self.cursor.description]
            employees = []
            for row in self.cursor.fetchall():
                employee = dict(zip(columns, row))
                employees.append(employee)
            return employees
        except sqlite3.Error as e:
            print(f"获取部门员工失败: {e}")
            return [] 
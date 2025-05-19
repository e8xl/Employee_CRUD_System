import os
import pandas as pd
import sqlite3
import traceback
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('employee_db.sqlite')
cursor = conn.cursor()

def log_operation(user, operation, details):
    """记录操作日志"""
    try:
        timestamp = datetime.now()
        cursor.execute('''
        INSERT INTO operation_logs (user, operation, details, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (user, operation, details, timestamp))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"记录操作日志失败: {e}")
        return False

def import_aut_department(file_path, year=2023, user="系统"):
    """导入AUT部门.csv的技能评分数据"""
    try:
        print(f"开始导入AUT部门数据: {file_path}")
        
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith('.csv'):
            # 尝试不同编码读取文件
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='gb18030')
                except:
                    df = pd.read_csv(file_path, encoding='latin1')
        else:
            print("不支持的文件格式")
            return False
        
        count_added = 0
        
        # 查找数据起始行
        start_row = None
        # 查找含有数字的第一行作为起始行
        for i, row in df.iterrows():
            if pd.notna(row.iloc[0]) and (isinstance(row.iloc[0], (int, float)) or 
                (isinstance(row.iloc[0], str) and row.iloc[0].isdigit())):
                start_row = i
                break
        
        # 如果找不到起始行，尝试查找"序号"行的下一行
        if start_row is None:
            for i, row in df.iterrows():
                if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == "序号":
                    start_row = i + 1
                    break
        
        # 如果还找不到，默认使用第20行 (AUT部门.csv通常在这一行开始数据)
        if start_row is None:
            start_row = 20  
        
        print(f"数据起始行: {start_row}")
        
        # 获取数据行
        data_rows = df.iloc[start_row:]
        
        # 提前获取技能代码行
        skill_codes_row = None
        for i in range(0, start_row):
            row_values = df.iloc[i].astype(str)
            if ('C01' in row_values.values or 'RUB' in row_values.values or 
                'USB' in row_values.values or 'AQR' in row_values.values):
                skill_codes_row = df.iloc[i]
                print(f"找到技能代码行: {i}")
                break
        
        # 处理每条员工数据
        for _, row in data_rows.iterrows():
            # 检查员工号是否存在
            if pd.isna(row.iloc[1]) or str(row.iloc[1]).strip() == "":
                continue
            
            # 获取员工号
            try:
                employee_no = str(int(row.iloc[1])) if pd.notna(row.iloc[1]) else ""
            except:
                employee_no = str(row.iloc[1]).strip()
            
            if not employee_no:
                continue
            
            # 查找员工ID
            cursor.execute("SELECT id FROM employees WHERE employee_no = ?", (employee_no,))
            result = cursor.fetchone()
            if not result:
                print(f"未找到工号为{employee_no}的员工，尝试创建...")
                # 创建新员工
                name = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else "未知"
                department = "AUT"
                
                cursor.execute("""
                INSERT INTO employees 
                (employee_no, name, department, status)
                VALUES (?, ?, ?, ?)
                """, (employee_no, name, department, "在职"))
                conn.commit()
                
                cursor.execute("SELECT id FROM employees WHERE employee_no = ?", (employee_no,))
                result = cursor.fetchone()
                if not result:
                    print(f"创建员工{employee_no}失败，跳过")
                    continue
            
            employee_id = result[0]
            
            # 提取评分数据 - AUT部门.csv中通常在最后几列
            try:
                # 先尝试从固定位置提取
                total_score_idx = -2
                skill_fields = {
                    'basic_knowledge_score': -7,
                    'position_skill_score': -6,
                    'cross_department_score': -5,
                    'technician_skill_score': -4,
                    'management_skill_score': -3,
                    'total_score': -2
                }
                
                scores = {}
                for field, idx in skill_fields.items():
                    try:
                        value = row.iloc[idx]
                        if pd.notna(value):
                            # 处理可能的格式问题，比如有空格的字符串
                            if isinstance(value, str):
                                value = value.strip()
                            scores[field] = float(value)
                        else:
                            scores[field] = 0
                    except (ValueError, IndexError, TypeError):
                        scores[field] = 0
                        
                # 验证是否提取到合理的分数
                if scores['total_score'] <= 0 or scores['total_score'] > 200:
                    # 重新尝试找总分，通常是一个较大的数（如70-200）
                    for i in range(-10, 0):
                        try:
                            value = row.iloc[i]
                            if pd.notna(value):
                                val = float(str(value).strip())
                                if 20 <= val <= 200:
                                    scores['total_score'] = val
                                    total_score_idx = i
                                    break
                        except:
                            continue
                
                # 如果已找到总分，尝试向前寻找其他分数
                if scores['total_score'] > 0:
                    # 基础知识分数通常是一个接近90的值
                    for i in range(total_score_idx-5, total_score_idx):
                        try:
                            value = row.iloc[i]
                            if pd.notna(value):
                                val = float(str(value).strip())
                                if 70 <= val <= 100:
                                    scores['basic_knowledge_score'] = val
                                    break
                        except:
                            continue
                
                print(f"员工{employee_no}的评分: 基础知识={scores['basic_knowledge_score']}, 岗位技能={scores['position_skill_score']}, " +
                        f"跨部门={scores['cross_department_score']}, 技师={scores['technician_skill_score']}, " +
                        f"管理={scores['management_skill_score']}, 总分={scores['total_score']}")
                
                # 插入或更新技能评分记录
                cursor.execute("""
                INSERT INTO skill_scores 
                (employee_id, year, basic_knowledge_score, position_skill_score, 
                cross_department_score, technician_skill_score, management_skill_score,
                total_score, evaluated_grade)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(employee_id, year) 
                DO UPDATE SET 
                    basic_knowledge_score = ?, position_skill_score = ?, 
                    cross_department_score = ?, technician_skill_score = ?,
                    management_skill_score = ?, total_score = ?, evaluated_grade = ?,
                    updated_at = CURRENT_TIMESTAMP
                """, (
                    employee_id, year, scores['basic_knowledge_score'], scores['position_skill_score'],
                    scores['cross_department_score'], scores['technician_skill_score'], 
                    scores['management_skill_score'], scores['total_score'], 'G1',  # 暂时使用G1
                    scores['basic_knowledge_score'], scores['position_skill_score'],
                    scores['cross_department_score'], scores['technician_skill_score'], 
                    scores['management_skill_score'], scores['total_score'], 'G1'  # 暂时使用G1
                ))
                
                conn.commit()
                
                # 获取skill_score_id
                cursor.execute("""
                SELECT id FROM skill_scores 
                WHERE employee_id = ? AND year = ?
                """, (employee_id, year))
                
                skill_score_id = cursor.fetchone()[0]
                
                # 处理技能明细分数
                # 先清除旧记录
                cursor.execute("DELETE FROM skill_detail_scores WHERE skill_score_id = ?", (skill_score_id,))
                
                # 如果找到了技能代码行，根据代码添加详细技能分数
                if skill_codes_row is not None:
                    # 遍历技能项并添加详细分数
                    for i in range(3, min(len(row) - 7, len(skill_codes_row))):  # 跳过序号、工号、姓名和总分列
                        try:
                            skill_value = row.iloc[i]
                            if pd.isna(skill_value) or skill_value == '':
                                continue
                            
                            skill_score = int(skill_value)
                            skill_code = str(skill_codes_row.iloc[i]).strip() if pd.notna(skill_codes_row.iloc[i]) else f"技能{i}"
                            
                            # 确定技能类型
                            skill_type = "基础知识"  # 默认为基础知识
                            if i < 13:
                                skill_type = "基础知识"
                            elif i < 45:
                                skill_type = "岗位技能"
                            elif i < 48:
                                skill_type = "跨部门技能"
                            elif i < 50:
                                skill_type = "技师技能"
                            else:
                                skill_type = "一线管理技能"
                            
                            cursor.execute("""
                            INSERT INTO skill_detail_scores
                            (skill_score_id, skill_code, skill_name, skill_type, skill_score)
                            VALUES (?, ?, ?, ?, ?)
                            """, (
                                skill_score_id, skill_code, skill_code, skill_type, skill_score
                            ))
                        except Exception as e:
                            print(f"添加技能{i}失败: {e}")
                            continue
                
                conn.commit()
                count_added += 1
                
            except Exception as e:
                print(f"处理员工{employee_no}的评分数据失败: {e}")
                traceback.print_exc()
                continue
        
        # 记录操作日志
        log_operation(
            user, 
            '导入AUT部门技能评分', 
            f"从{os.path.basename(file_path)}导入{year}年技能评分数据，成功添加/更新{count_added}条记录"
        )
        
        print(f"成功导入{count_added}条记录")
        return True
    
    except Exception as e:
        print(f"导入AUT部门技能评分失败: {e}")
        traceback.print_exc()
        return False

def import_aut_exam(file_path, year=2023, user="系统"):
    """处理AUT笔试成绩.csv文件的导入"""
    try:
        print(f"开始导入AUT笔试成绩: {file_path}")
        
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith('.csv'):
            # 尝试不同编码读取文件
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='gb18030')
                except:
                    df = pd.read_csv(file_path, encoding='latin1')
        else:
            print("不支持的文件格式")
            return False
        
        count_added = 0
        
        # 遍历所有行
        for _, row in df.iterrows():
            # 找到员工号列
            employee_no_col = 0
            
            # 默认员工号在第一列
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip().isdigit():
                employee_no_col = 0
            # 否则可能在第二列
            elif len(row) > 1 and pd.notna(row.iloc[1]) and str(row.iloc[1]).strip().isdigit():
                employee_no_col = 1
            else:
                # 若前两列都不是数字，则跳过此行
                continue
            
            try:
                employee_no = str(int(row.iloc[employee_no_col])) if pd.notna(row.iloc[employee_no_col]) else ""
            except:
                # 如果无法转为整数，可能是标题行或其他非数据行
                continue
            
            # 查找员工ID
            cursor.execute("SELECT id FROM employees WHERE employee_no = ?", (employee_no,))
            result = cursor.fetchone()
            if not result:
                print(f"未找到工号为{employee_no}的员工，尝试创建...")
                # 创建新员工
                name_col = employee_no_col + 1 if employee_no_col + 1 < len(row) else employee_no_col
                name = str(row.iloc[name_col]) if pd.notna(row.iloc[name_col]) else "未知"
                department = "AUT"
                
                cursor.execute("""
                INSERT INTO employees 
                (employee_no, name, department, status)
                VALUES (?, ?, ?, ?)
                """, (employee_no, name, department, "在职"))
                conn.commit()
                
                cursor.execute("SELECT id FROM employees WHERE employee_no = ?", (employee_no,))
                result = cursor.fetchone()
                if not result:
                    print(f"创建员工{employee_no}失败，跳过")
                    continue
            
            employee_id = result[0]
            
            # 提取基础知识成绩，默认为90分
            basic_knowledge_score = 90
            
            # 尝试找到分数列
            for i in range(len(row)):
                if i == employee_no_col:
                    continue
                    
                try:
                    value = row.iloc[i]
                    if pd.notna(value):
                        if isinstance(value, (int, float)):
                            score = float(value)
                        elif isinstance(value, str) and value.strip().isdigit():
                            score = float(value.strip())
                        else:
                            continue
                            
                        if 0 < score <= 100:
                            basic_knowledge_score = score
                            break
                except:
                    continue
            
            # 查询员工当前评分记录
            cursor.execute("""
            SELECT id, evaluated_grade, position_skill_score, cross_department_score,
                   technician_skill_score, management_skill_score, total_score
            FROM skill_scores 
            WHERE employee_id = ? AND year = ?
            """, (employee_id, year))
            
            existing_score = cursor.fetchone()
            
            if existing_score:
                # 已有记录，更新基础知识分数
                score_id, grade, position_score, cross_score, tech_score, mgmt_score, total = existing_score
                
                # 重新计算总分
                new_total = basic_knowledge_score + (position_score or 0) + (cross_score or 0) + (tech_score or 0) + (mgmt_score or 0)
                
                # 使用已有的职级
                evaluated_grade = grade
                
                cursor.execute("""
                UPDATE skill_scores
                SET basic_knowledge_score = ?, total_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """, (basic_knowledge_score, new_total, score_id))
                
            else:
                # 没有记录，插入新记录
                cursor.execute("""
                INSERT INTO skill_scores 
                (employee_id, year, basic_knowledge_score, total_score, evaluated_grade)
                VALUES (?, ?, ?, ?, ?)
                """, (employee_id, year, basic_knowledge_score, basic_knowledge_score, 'G1'))  # 暂时使用G1
            
            conn.commit()
            count_added += 1
            
            print(f"员工{employee_no}的笔试成绩: {basic_knowledge_score}")
        
        # 记录操作日志
        log_operation(
            user, 
            '导入AUT笔试成绩', 
            f"从{os.path.basename(file_path)}导入{year}年笔试成绩，成功添加/更新{count_added}条记录"
        )
        
        print(f"成功导入{count_added}条记录")
        return True
        
    except Exception as e:
        print(f"导入AUT笔试成绩失败: {e}")
        traceback.print_exc()
        return False

def import_aut_thresholds(file_path, year=2023, user="系统"):
    """导入AUT计算方法和标准.csv的职级阈值数据"""
    try:
        print(f"开始导入AUT职级阈值: {file_path}")
        
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith('.csv'):
            # 尝试不同编码读取文件
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='gb18030')
                except:
                    df = pd.read_csv(file_path, encoding='latin1')
        else:
            print("不支持的文件格式")
            return False
            
        count_added = 0
        
        # 查找包含G1-G4B的行
        threshold_rows = []
        
        # 尝试在第一列查找职级
        for i, row in df.iterrows():
            cell_value = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            if any(grade in cell_value for grade in ['G1', 'G2', 'G3', 'G4A', 'G4B']):
                threshold_rows.append((i, row))
        
        if not threshold_rows:
            print("未找到职级阈值数据")
            return False
        
        print(f"找到{len(threshold_rows)}行职级阈值数据")
        
        # 处理每个职级阈值
        for row_idx, row in threshold_rows:
            # 确定职级
            cell_value = str(row.iloc[0])
            if 'G1' in cell_value:
                grade = 'G1'
            elif 'G2' in cell_value:
                grade = 'G2'
            elif 'G3' in cell_value:
                grade = 'G3'
            elif 'G4A' in cell_value:
                grade = 'G4A'
            elif 'G4B' in cell_value:
                grade = 'G4B'
            else:
                continue
            
            # 遍历行，查找阈值数据
            basic_knowledge_min = 0
            position_skill_min = 0
            cross_department_min = 0
            technician_skill_min = 0
            management_skill_min = 0
            total_min = 0
            
            # 首先尝试查找总分阈值，通常是一个较大的数值
            for i in range(1, min(len(row), 20)):
                try:
                    val = float(row.iloc[i]) if pd.notna(row.iloc[i]) else 0
                    if 20 <= val <= 200:  # 总分通常在这个范围内
                        total_min = val
                        break
                except:
                    continue
            
            # 基于AUT计算方法和标准.csv的结构，查找各项分数阈值
            # 通常在32-36行左右的区域
            for i, search_row in df.iterrows():
                if i < 30 or i > 40:  # 限制搜索范围
                    continue
                    
                cell_value = str(search_row.iloc[0]) if pd.notna(search_row.iloc[0]) else ""
                if grade in cell_value:
                    try:
                        # 根据AUT阈值文件的结构取值
                        if len(search_row) >= 4:
                            basic_knowledge_min = float(search_row.iloc[1]) if pd.notna(search_row.iloc[1]) else 0
                            position_skill_min = float(search_row.iloc[2]) if pd.notna(search_row.iloc[2]) else 0
                            
                            # 其他阈值可能在后面几列
                            for j in range(3, min(len(search_row), 8)):
                                val = float(search_row.iloc[j]) if pd.notna(search_row.iloc[j]) else 0
                                if j == 3:
                                    cross_department_min = val
                                elif j == 4:
                                    technician_skill_min = val
                                elif j == 5:
                                    management_skill_min = val
                                elif j == 6 and total_min == 0:
                                    total_min = val
                            
                            break
                    except Exception as e:
                        print(f"提取{grade}阈值数据出错: {e}")
            
            # 确保职级阈值合理，避免错误数据影响评级
            if grade == 'G1' and total_min < 10:
                total_min = 20
            elif grade == 'G2' and total_min < 30:
                total_min = 44
            elif grade == 'G3' and total_min < 50:
                total_min = 60
            elif grade == 'G4A' and total_min < 80:
                total_min = 94
            elif grade == 'G4B' and total_min < 90:
                total_min = 102
            
            print(f"职级{grade}的阈值: 基础知识={basic_knowledge_min}, 岗位技能={position_skill_min}, " +
                  f"跨部门={cross_department_min}, 技师={technician_skill_min}, " +
                  f"管理={management_skill_min}, 总分={total_min}")
            
            # 插入或更新阈值记录
            cursor.execute("""
            INSERT INTO skill_thresholds
            (year, grade, basic_knowledge_min, position_skill_min, cross_department_min,
            technician_skill_min, management_skill_min, total_min)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(year, grade) 
            DO UPDATE SET 
                basic_knowledge_min = ?, position_skill_min = ?, cross_department_min = ?,
                technician_skill_min = ?, management_skill_min = ?, total_min = ?,
                updated_at = CURRENT_TIMESTAMP
            """, (
                year, grade, basic_knowledge_min, position_skill_min, cross_department_min,
                technician_skill_min, management_skill_min, total_min,
                basic_knowledge_min, position_skill_min, cross_department_min,
                technician_skill_min, management_skill_min, total_min
            ))
            
            conn.commit()
            count_added += 1
        
        # 记录操作日志
        log_operation(
            user, 
            '导入AUT职级阈值', 
            f"从{os.path.basename(file_path)}导入{year}年职级评定阈值，成功添加/更新{count_added}条记录"
        )
        
        print(f"成功导入{count_added}条记录")
        return True
        
    except Exception as e:
        print(f"导入AUT阈值数据失败: {e}")
        traceback.print_exc()
        return False

def update_employee_grades(year=2023, user="系统"):
    """更新员工职级"""
    try:
        print(f"开始计算{year}年职级...")
        
        # 获取所有职级阈值
        cursor.execute("""
        SELECT grade, basic_knowledge_min, position_skill_min, cross_department_min,
            technician_skill_min, management_skill_min, total_min
        FROM skill_thresholds
        WHERE year = ?
        ORDER BY total_min DESC
        """, (year,))
        
        thresholds = cursor.fetchall()
        
        if not thresholds:
            print("未找到职级阈值数据，使用默认阈值")
            thresholds = [
                ('G4B', 100, 183.6, 0, 0, 100, 102),
                ('G4A', 100, 163.2, 0, 100, 0, 94),
                ('G3', 100, 102, 0, 0, 0, 60),
                ('G2', 100, 61.2, 0, 0, 0, 44),
                ('G1', 100, 0, 0, 0, 0, 20)
            ]
        
        # 获取所有员工评分
        cursor.execute("""
        SELECT id, employee_id, basic_knowledge_score, position_skill_score, 
            cross_department_score, technician_skill_score, management_skill_score,
            total_score
        FROM skill_scores
        WHERE year = ?
        """, (year,))
        
        scores = cursor.fetchall()
        
        count_updated = 0
        
        for score in scores:
            score_id, employee_id, bk_score, ps_score, cd_score, ts_score, ms_score, total_score = score
            
            # 如果总分为0，跳过
            if total_score <= 0:
                continue
                
            # 根据阈值判断职级
            evaluated_grade = 'G1'  # 默认最低职级
            
            for threshold in thresholds:
                grade, bk_min, ps_min, cd_min, ts_min, ms_min, total_min = threshold
                
                if (total_score >= total_min and 
                    bk_score >= bk_min and 
                    ps_score >= ps_min):
                    
                    # 额外检查特定职级的特殊要求
                    if grade == 'G4B' and ms_score >= ms_min:
                        evaluated_grade = grade
                        break
                    elif grade == 'G4A' and ts_score >= ts_min:
                        evaluated_grade = grade
                        break
                    elif grade in ['G3', 'G2', 'G1']:
                        evaluated_grade = grade
                        break
            
            # 更新职级
            cursor.execute("""
            UPDATE skill_scores
            SET evaluated_grade = ?
            WHERE id = ?
            """, (evaluated_grade, score_id))
            
            # 更新员工表中的职级
            cursor.execute(f"""
            UPDATE employees
            SET grade_{year} = ?
            WHERE id = ?
            """, (evaluated_grade, employee_id))
            
            conn.commit()
            count_updated += 1
            
            # 打印更新信息
            cursor.execute("SELECT employee_no, name FROM employees WHERE id = ?", (employee_id,))
            employee = cursor.fetchone()
            if employee:
                employee_no, name = employee
                print(f"员工 {employee_no} ({name}) 的{year}年职级: {evaluated_grade}, 总分: {total_score}")
        
        # 记录操作日志
        log_operation(
            user,
            '更新员工职级',
            f"更新{year}年员工职级，成功更新{count_updated}条记录"
        )
        
        print(f"成功更新{count_updated}条职级记录")
        return True
        
    except Exception as e:
        print(f"更新员工职级失败: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        # 设置导入年份
        year = 2023
        
        # 导入AUT职级阈值
        import_aut_thresholds("data/AUT/AUT_计算方法和标准.csv", year)
        
        # 导入AUT笔试成绩
        import_aut_exam("data/AUT/AUT_笔试成绩.csv", year)
        
        # 导入AUT部门技能评分
        import_aut_department("data/AUT/AUT部门.csv", year)
        
        # 更新员工职级
        update_employee_grades(year)
        
        print("AUT部门数据导入完成")
        
    except Exception as e:
        print(f"导入过程中出错: {e}")
        traceback.print_exc()
    finally:
        conn.close() 
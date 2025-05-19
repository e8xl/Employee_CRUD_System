import sqlite3

# 连接数据库
conn = sqlite3.connect('employee_db.sqlite')
cursor = conn.cursor()

# 查询技能评分记录数
cursor.execute('SELECT COUNT(*) FROM skill_scores')
score_count = cursor.fetchone()[0]
print(f'已导入技能评分记录数: {score_count}')

# 查询职级阈值记录数
cursor.execute('SELECT COUNT(*) FROM skill_thresholds')
threshold_count = cursor.fetchone()[0]
print(f'已导入职级阈值记录数: {threshold_count}')

# 查询员工技能明细记录数
cursor.execute('SELECT COUNT(*) FROM skill_detail_scores')
detail_count = cursor.fetchone()[0]
print(f'已导入技能明细记录数: {detail_count}')

# 查询每个部门的员工数量
cursor.execute('SELECT department, COUNT(*) FROM employees GROUP BY department')
departments = cursor.fetchall()
print('各部门员工数量:')
for dept, count in departments:
    print(f'  {dept or "未分配"}: {count}人')

# 查询每个职级的人数(2023年)
cursor.execute('SELECT evaluated_grade, COUNT(*) FROM skill_scores WHERE year=2023 GROUP BY evaluated_grade')
grades = cursor.fetchall()
print('2023年职级分布:')
for grade, count in grades:
    print(f'  {grade or "未评级"}: {count}人')

# 关闭连接
cursor.close()
conn.close() 
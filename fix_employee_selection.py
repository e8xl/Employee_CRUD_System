"""
修复员工选择问题的脚本

此脚本会修改app/views/aut_score_view.py文件中的员工选择和处理逻辑，
确保即使ComboBox的currentData返回None，也能正确获取员工编号。
"""

import os
import re

# 目标文件路径
target_file = 'app/views/aut_score_view.py'

# 备份文件路径
backup_file = 'app/views/aut_score_view.py.bak'

# 确保文件存在
if not os.path.exists(target_file):
    print(f"错误: 找不到目标文件 {target_file}")
    exit(1)

# 创建备份
try:
    with open(target_file, 'r', encoding='utf-8') as src:
        content = src.read()
    
    with open(backup_file, 'w', encoding='utf-8') as dest:
        dest.write(content)
    
    print(f"已创建备份文件: {backup_file}")
except Exception as e:
    print(f"创建备份时出错: {e}")
    exit(1)

# 定义要替换的函数内容
old_on_employee_selected = r"""    def on_employee_selected\(\):
        \"\"\"员工选择变化处理\"\"\"
        emp_no = self\.employee_combo\.currentData\(\)
        
        if not emp_no:
            self\.current_employee_no = None
            return
            
        self\.current_employee_no = emp_no
        self\.load_scores\(\)
        
        # 确认当前员工已选中
        InfoBar\.success\(
            title='已选择员工',
            content=f'当前选择: {self\.employee_combo\.currentText\(\)}',
            parent=self,
            position=InfoBarPosition\.TOP,
            duration=2000
        \)"""

# 新版本的on_employee_selected函数
new_on_employee_selected = '''    def on_employee_selected(self):
        """员工选择变化处理"""
        # 获取当前选中的员工编号
        selected_index = self.employee_combo.currentIndex()
        selected_text = self.employee_combo.currentText()
        emp_no = self.employee_combo.currentData()
        
        print(f"【员工选择】索引: {selected_index}, 文本: {selected_text}, 数据值: {emp_no}")
        
        # 直接从显示文本中解析员工编号
        if selected_index > 0 and not emp_no:
            # 尝试从显示的文本中解析员工编号 "姓名 (工号)"
            try:
                if \'(\' in selected_text and \')\' in selected_text:
                    emp_no_text = selected_text.split("(")[1].strip(")")
                    print(f"【员工选择】从文本解析的员工编号: {emp_no_text}")
                    emp_no = emp_no_text
            except Exception as e:
                print(f"【员工选择】解析员工编号失败: {e}")
        
        if not emp_no:
            self.current_employee_no = None
            
            if selected_index > 0:
                # 如果选择了真实员工但未获取到编号，显示错误
                InfoBar.error(
                    title=\'错误\',
                    content=\'无法获取员工编号，请联系管理员\',
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
            return
            
        self.current_employee_no = emp_no
        print(f"【员工选择】成功设置当前员工编号: {self.current_employee_no}")
        self.load_scores()
        
        # 确认当前员工已选中
        InfoBar.success(
            title=\'已选择员工\',
            content=f\'当前选择: {selected_text} (编号: {emp_no})\',
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )'''

# 定义要替换的calculate_grade函数
old_calculate_grade_pattern = r"""        # 如果current_employee_no为None但界面已选择员工，则重新获取员工编号
        if not self\.current_employee_no and self\.employee_combo\.currentData\(\):
            self\.current_employee_no = self\.employee_combo\.currentData\(\)
            
        if not self\.current_employee_no:"""

# 新版本的calculate_grade函数相关代码
new_calculate_grade_pattern = '''        # 如果current_employee_no为None但界面已选择员工，则重新获取员工编号
        if not self.current_employee_no and self.employee_combo.currentIndex() > 0:
            # 尝试从界面获取员工编号
            emp_no = self.employee_combo.currentData()
            selected_text = self.employee_combo.currentText()
            
            # 如果currentData返回None，尝试从文本解析
            if not emp_no and \'(\' in selected_text and \')\' in selected_text:
                try:
                    emp_no = selected_text.split("(")[1].strip(")")
                    print(f"【计算职级】从文本解析的员工编号: {emp_no}")
                    self.current_employee_no = emp_no
                except Exception as e:
                    print(f"【计算职级】解析员工编号失败: {e}")
            else:
                self.current_employee_no = emp_no
                
            print(f"【计算职级】设置员工编号: {self.current_employee_no}")
            
        if not self.current_employee_no:'''

# 定义要替换的save_scores函数
old_save_scores_pattern = r"""        # 如果current_employee_no为None但界面已选择员工，则重新获取员工编号
        if not self\.current_employee_no and self\.employee_combo\.currentData\(\):
            self\.current_employee_no = self\.employee_combo\.currentData\(\)
            
        if not self\.current_employee_no:"""

# 新版本的save_scores函数相关代码
new_save_scores_pattern = '''        # 如果current_employee_no为None但界面已选择员工，则重新获取员工编号
        if not self.current_employee_no and self.employee_combo.currentIndex() > 0:
            # 尝试从界面获取员工编号
            emp_no = self.employee_combo.currentData()
            selected_text = self.employee_combo.currentText()
            
            # 如果currentData返回None，尝试从文本解析
            if not emp_no and \'(\' in selected_text and \')\' in selected_text:
                try:
                    emp_no = selected_text.split("(")[1].strip(")")
                    print(f"【保存成绩】从文本解析的员工编号: {emp_no}")
                    self.current_employee_no = emp_no
                except Exception as e:
                    print(f"【保存成绩】解析员工编号失败: {e}")
            else:
                self.current_employee_no = emp_no
                
            print(f"【保存成绩】设置员工编号: {self.current_employee_no}")
            
        if not self.current_employee_no:'''

# 应用修改
try:
    # 读取文件内容
    with open(target_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 替换on_employee_selected函数
    new_content = re.sub(old_on_employee_selected, new_on_employee_selected, content)
    
    # 替换calculate_grade函数中的检查部分
    new_content = re.sub(old_calculate_grade_pattern, new_calculate_grade_pattern, new_content)
    
    # 替换save_scores函数中的检查部分
    new_content = re.sub(old_save_scores_pattern, new_save_scores_pattern, new_content)
    
    # 保存修改后的内容
    with open(target_file, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print("修复已完成！")
    print("现在AUT成绩录入界面应该能够正确识别选择的员工了。")
    print("即使下拉框返回None值，程序也会尝试从显示文本中解析员工编号。")
except Exception as e:
    print(f"修复过程中出错: {e}")
    print(f"将尝试从备份文件恢复: {backup_file}")
    
    try:
        # 如果出错，恢复备份
        with open(backup_file, 'r', encoding='utf-8') as src:
            backup_content = src.read()
        
        with open(target_file, 'w', encoding='utf-8') as dest:
            dest.write(backup_content)
        
        print("已从备份文件恢复原始文件。")
    except Exception as restore_error:
        print(f"恢复备份时出错: {restore_error}")
        print(f"请手动从备份文件恢复: {backup_file}") 
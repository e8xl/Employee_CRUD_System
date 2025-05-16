import os
import sys

def get_resource_path(relative_path):
    """获取资源文件的绝对路径
    
    参数:
        relative_path (str): 相对于应用根目录的资源文件路径
        
    返回:
        str: 资源文件的绝对路径
    """
    # 获取应用根目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的应用
        app_path = os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        # 从当前文件所在目录回溯到应用根目录
        app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    # 构建资源文件的绝对路径
    return os.path.normpath(os.path.join(app_path, relative_path))

def ensure_dir(dir_path):
    """确保目录存在，如果不存在则创建
    
    参数:
        dir_path (str): 目录路径
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        
def get_theme_resources(theme="light"):
    """获取主题相关资源的路径
    
    参数:
        theme (str): 主题名称，默认为"light"
        
    返回:
        dict: 包含各类主题资源路径的字典
    """
    theme_path = get_resource_path(f"app/resources/qss/{theme}")
    
    return {
        "style": os.path.join(theme_path, "style.qss") if os.path.exists(os.path.join(theme_path, "style.qss")) else None,
        "icons": get_resource_path(f"app/resources/icons/{theme}"),
        "images": get_resource_path("app/resources/images")
    } 
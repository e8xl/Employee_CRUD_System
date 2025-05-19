# 员工管理系统资源文件

此目录包含应用程序使用的所有资源文件。

## 目录结构

- `/qss` - 样式表文件
  - `/light` - 亮色主题样式表
  - `/dark` - 暗色主题样式表
- `/icons` - 图标文件
  - `/light` - 亮色主题图标
  - `/dark` - 暗色主题图标
- `/images` - 图像文件

## 使用说明

使用 `resource_loader.py` 中的 `get_resource_path()` 函数来获取资源文件的绝对路径。

```python
from app.utils.resource_loader import get_resource_path

# 获取图像文件路径
image_path = get_resource_path('app/resources/images/logo.png')

# 获取当前主题的样式表
theme = 'dark' if isDarkTheme() else 'light'
style_path = get_resource_path(f'app/resources/qss/{theme}/style.qss')
```

## 样式指南

应用程序使用 QtFluentWidgets 实现 Fluent Design 风格的界面。样式指南详见 `qss/style_guide.md`。 
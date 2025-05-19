# QtFluentWidgets 风格设计指南

本文档提供了使用 QtFluentWidgets 设计 PyQt 应用程序的标准指南和最佳实践。

## 目录

1. [基本设计原则](#基本设计原则)
2. [窗口结构](#窗口结构)
3. [导航设计](#导航设计)
4. [内容布局](#内容布局)
5. [组件选择](#组件选择)
6. [颜色与主题](#颜色与主题)
7. [交互反馈](#交互反馈)
8. [响应式设计](#响应式设计)
9. [最佳实践](#最佳实践)

## 基本设计原则

Fluent Design 系统基于以下五个关键元素：

- **光线(Light)**: 使用光线效果引导注意力
- **深度(Depth)**: 创建层次感
- **动作(Motion)**: 使用自然且有意义的动画
- **材质(Material)**: 使用视觉元素模拟物理材质
- **比例(Scale)**: 适应不同屏幕大小和交互方式

在 QtFluentWidgets 中实现上述原则时，应当关注：

- 简洁性：界面应当简洁明了，避免过度设计
- 一致性：保持视觉和交互的一致性
- 层次感：通过卡片、阴影等元素创建视觉层次
- 反馈：为用户操作提供明确的视觉反馈
- 可访问性：确保界面易于使用和理解

## 窗口结构

### 主窗口

使用 `MSFluentWindow` 作为主窗口基类，它提供了符合 Fluent Design 的窗口框架：

```python
from qfluentwidgets import MSFluentWindow

class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        # 窗口设置
        self.resize(1000, 650)
        self.setWindowTitle("应用名称")
        
        # 初始化导航栏和内容
        self.initNavigation()
        self.initWindow()
```

### 无边框窗口

对于需要自定义标题栏的应用，可以使用 `FramelessWindow`：

```python
from qframelesswindow import FramelessWindow, StandardTitleBar

class CustomWindow(FramelessWindow):
    def __init__(self):
        super().__init__()
        # 设置标准标题栏
        self.setTitleBar(StandardTitleBar(self))
        # 窗口设置
        self.resize(1000, 650)
```

## 导航设计

### 导航接口

使用 `NavigationInterface` 创建侧边导航栏：

```python
def initNavigation(self):
    # 设置导航栏宽度
    self.navigationInterface.setExpandWidth(260)
    self.navigationInterface.setMinimumWidth(48)
    
    # 添加导航项
    self.navigationInterface.addItem(
        routeKey='home',
        icon=FIF.HOME,
        text='主页',
        position=NavigationItemPosition.TOP,
        tooltip='返回主页'
    )
    
    # 添加分隔线
    self.navigationInterface.addSeparator()
    
    # 添加底部导航项
    self.navigationInterface.addItem(
        routeKey='settings',
        icon=FIF.SETTING,
        text='设置',
        position=NavigationItemPosition.BOTTOM,
        tooltip='应用设置'
    )
```

### 导航逻辑

绑定导航项点击事件：

```python
# 绑定导航点击事件
self.navigationInterface.clicked.connect(self.onNavigationClicked)

def onNavigationClicked(self, item):
    route_key = item.routeKey()
    
    if route_key == 'home':
        self.stackedWidget.setCurrentWidget(self.homeView)
    elif route_key == 'settings':
        self.stackedWidget.setCurrentWidget(self.settingsView)
```

## 内容布局

### 卡片布局

使用 `CardWidget` 包装内容区域，增强视觉层次：

```python
from qfluentwidgets import CardWidget

# 创建卡片容器
card = CardWidget(self)
card_layout = QVBoxLayout(card)
card_layout.setContentsMargins(20, 20, 20, 20)

# 添加内容到卡片中
card_layout.addWidget(content_widget)
```

### 间距与留白

合理设置布局的间距和留白：

```python
layout = QVBoxLayout(self)
layout.setContentsMargins(20, 20, 20, 20)  # 左、上、右、下边距
layout.setSpacing(16)  # 控件之间的间距
```

### 滚动区域

对于内容较多的页面，使用 `ScrollArea`：

```python
from qfluentwidgets import ScrollArea

# 创建滚动区域
scroll_area = ScrollArea(self)
scroll_area.setWidgetResizable(True)

# 创建内容容器
content = QWidget()
content_layout = QVBoxLayout(content)
content_layout.setContentsMargins(0, 0, 0, 0)
content_layout.setSpacing(10)

# 添加内容
for i in range(20):
    content_layout.addWidget(QLabel(f"Item {i}"))

# 设置滚动区域的内容
scroll_area.setWidget(content)
```

## 组件选择

### 基础输入组件

- 按钮：使用 `PushButton`、`PrimaryPushButton`、`TransparentPushButton` 等
- 输入框：使用 `LineEdit`、`SearchLineEdit` 等
- 下拉框：使用 `ComboBox`
- 复选框：使用 `CheckBox`
- 单选按钮：使用 `RadioButton`

### 表格和列表

- 表格：使用 `TableWidget` 替代 `QTableView`
- 列表：使用 `ListWidget` 替代 `QListView`

### 工具提示

使用 `ToolTipFilter` 添加自定义工具提示：

```python
from qfluentwidgets import ToolTipFilter, ToolTipPosition

button = PushButton('按钮', self)
button.installEventFilter(ToolTipFilter(button, showDelay=500))
button.setToolTip('这是一个按钮')
button.setToolTipDuration(2000)
```

## 颜色与主题

### 主题设置

在应用启动时设置主题：

```python
from qfluentwidgets import setTheme, Theme, setThemeColor

# 设置主题模式（亮色/暗色/自动）
setTheme(Theme.AUTO)

# 设置主题颜色
setThemeColor('#0078d4')  # Fluent蓝色
```

### 主题切换

支持动态切换主题：

```python
def toggleTheme(self):
    if isDarkTheme():
        setTheme(Theme.LIGHT)
    else:
        setTheme(Theme.DARK)
    
    # 更新样式表
    self.setQss()
```

### 样式表

根据当前主题加载相应的样式表：

```python
def setQss(self):
    # 根据当前主题选择样式表
    theme = 'dark' if isDarkTheme() else 'light'
    with open(f'resources/qss/{theme}/style.qss', encoding='utf-8') as f:
        self.setStyleSheet(f.read())
```

## 交互反馈

### 消息提示

使用 `InfoBar` 显示消息提示：

```python
from qfluentwidgets import InfoBar, InfoBarPosition

# 成功消息
InfoBar.success(
    title='操作成功',
    content='数据已保存',
    orient=Qt.Horizontal,
    isClosable=True,
    position=InfoBarPosition.TOP,
    duration=3000,
    parent=self
)

# 错误消息
InfoBar.error(
    title='操作失败',
    content='保存数据时发生错误',
    orient=Qt.Horizontal,
    isClosable=True,
    position=InfoBarPosition.TOP,
    duration=5000,
    parent=self
)
```

### 对话框

使用 `MessageBox` 或 `Dialog` 显示对话框：

```python
from qfluentwidgets import MessageBox

dialog = MessageBox(
    '确认操作',
    '确定要执行此操作吗？',
    self
)

yes_btn = dialog.addButton('确定', True)
no_btn = dialog.addButton('取消', False)
dialog.setDefaultButton(no_btn)

if dialog.exec_():
    # 用户点击了确定按钮
    pass
```

### 状态提示

使用 `StateToolTip` 显示操作状态：

```python
from qfluentwidgets import StateToolTip

# 显示加载状态
state_tooltip = StateToolTip('正在加载', '正在处理数据...', self)
state_tooltip.show()

# 操作完成后更新状态
state_tooltip.setContent('处理完成')
state_tooltip.setState(True)
```

## 响应式设计

### 自适应布局

使用布局管理器和弹性空间确保界面在不同大小的窗口中正常显示：

```python
# 主布局
layout = QVBoxLayout(self)

# 顶部固定高度的工具栏
layout.addWidget(toolbar)

# 中间自适应的内容区域
layout.addWidget(content, 1)  # 1表示拉伸因子

# 底部固定高度的状态栏
layout.addWidget(statusbar)
```

### 分割器

使用 `QSplitter` 创建可调整大小的区域：

```python
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtCore import Qt

# 创建水平分割器
splitter = QSplitter(Qt.Horizontal)
splitter.addWidget(left_panel)
splitter.addWidget(right_panel)

# 设置初始大小比例
splitter.setSizes([300, 700])
```

## 最佳实践

1. **模块化设计**：将UI组件分为独立的类和文件，便于维护
2. **资源管理**：使用资源加载器统一管理应用资源
3. **信号与槽**：使用信号和槽机制进行组件间通信
4. **异步处理**：将耗时操作放在单独的线程中执行
5. **错误处理**：为所有可能的错误提供友好的用户反馈
6. **配置保存**：保存窗口大小、位置和用户偏好
7. **代码注释**：为类和方法添加清晰的文档字符串
8. **主题适配**：确保应用在亮色和暗色主题下都能正常显示
9. **高DPI支持**：确保应用在高DPI显示器上正确缩放
10. **国际化支持**：支持多语言界面，使用翻译机制 
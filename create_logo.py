from PIL import Image, ImageDraw, ImageFont
import os

def create_logo():
    # 创建一个512x512的透明背景图像
    size = (512, 512)
    image = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # 画一个圆形背景
    circle_center = (256, 256)
    circle_radius = 210
    # 蓝色背景，使用Fluent Design蓝色 #0078D4
    circle_color = (0, 120, 212, 255)
    draw.ellipse(
        (circle_center[0] - circle_radius, 
         circle_center[1] - circle_radius,
         circle_center[0] + circle_radius, 
         circle_center[1] + circle_radius), 
        fill=circle_color
    )
    
    # 添加文字 "EMS"
    try:
        # 尝试使用Arial字体，如果不可用则使用默认字体
        font = ImageFont.truetype("arial.ttf", 200)
    except IOError:
        font = ImageFont.load_default()
    
    # 白色文字
    text_color = (255, 255, 255)
    text = "EMS"
    
    # 计算文字位置以居中显示
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    text_position = (circle_center[0] - text_width // 2, circle_center[1] - text_height // 2 - 20)
    
    # 绘制文字
    draw.text(text_position, text, font=font, fill=text_color)
    
    # 确保目录存在
    os.makedirs("app/resources/images", exist_ok=True)
    
    # 保存图像
    image.save("app/resources/images/logo.png")
    
    print("Logo创建成功：app/resources/images/logo.png")

if __name__ == "__main__":
    create_logo() 
# -*- coding: utf-8 -*-
"""
生成小程序 tabBar 图标
运行: python generate_icons.py
"""
import os
from PIL import Image, ImageDraw

# 确保 assets 目录存在
assets_dir = os.path.dirname(os.path.abspath(__file__))

def create_icon(name, is_active=False):
    """创建图标"""
    size = 81
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 颜色
    if is_active:
        bg_color = (230, 247, 255, 255)  # #E6F7FF
        stroke_color = (24, 144, 255, 255)  # #1890FF
        fill_color = (24, 144, 255, 255)
    else:
        bg_color = (230, 230, 230, 255)  # #E6E6E6
        stroke_color = (102, 102, 102, 255)  # #666666
        fill_color = (102, 102, 102, 255)
    
    # 画圆形背景
    draw.ellipse([4, 4, size-4, size-4], fill=bg_color, outline=stroke_color, width=2)
    
    # 根据图标类型绘制
    if name == 'home':
        # 时钟/首页图标
        draw.line([(40, 22), (40, 40)], fill=fill_color, width=4)
        draw.line([(40, 40), (55, 55)], fill=fill_color, width=4)
        draw.ellipse([37, 37, 44, 44], fill=fill_color)
    elif name == 'stock':
        # 股票走势图
        points = [(22, 55), (32, 38), (42, 48), (52, 28), (60, 38)]
        for i in range(len(points)-1):
            draw.line([points[i], points[i+1]], fill=fill_color, width=3)
        for p in points:
            draw.ellipse([p[0]-3, p[1]-3, p[0]+3, p[1]+3], fill=fill_color)
    elif name == 'backtest':
        # 回测对比图标
        draw.polygon([(25, 50), (40, 28), (56, 50)], outline=fill_color, width=3)
        draw.polygon([(25, 50), (40, 65), (56, 50)], outline=fill_color, width=3)
        draw.line([(40, 28), (40, 65)], fill=fill_color, width=3)
    elif name == 'predict':
        # 预测/时钟图标
        draw.ellipse([20, 20, 60, 60], outline=fill_color, width=3)
        draw.line([(40, 24), (40, 40)], fill=fill_color, width=3)
        draw.line([(40, 40), (52, 40)], fill=fill_color, width=3)
    elif name == 'settings':
        # 设置/齿轮图标
        draw.ellipse([28, 24, 52, 48], outline=fill_color, width=3)
        draw.line([(40, 48), (40, 60)], fill=fill_color, width=4)
        draw.line([(30, 60), (50, 60)], fill=fill_color, width=4)
    
    return img

def main():
    icons = ['home', 'stock', 'backtest', 'predict', 'settings']
    
    for icon_name in icons:
        # 正常状态
        img_normal = create_icon(icon_name, is_active=False)
        img_normal.save(os.path.join(assets_dir, f'{icon_name}.png'))
        
        # 选中状态
        img_active = create_icon(icon_name, is_active=True)
        img_active.save(os.path.join(assets_dir, f'{icon_name}-active.png'))
        
        print(f'✓ 已生成 {icon_name}.png 和 {icon_name}-active.png')
    
    print('\n所有图标生成完成！')

if __name__ == '__main__':
    main()

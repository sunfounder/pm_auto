import numpy as np
import time
from PIL import Image

MAX_FRAME = 36
DEFAULT_COLOR = (255, 0, 0)
DEFAULT_COLOR2 = (0, 0, 255)
frame_index = 0

# Draw a 2 half rectangle matrix
def draw_2_half_rectangle_matrix(width=16, height=16, color=(255, 0, 0), color2=None):
    date = np.zeros((width, height, 3), dtype=np.uint8)
    center_x = width / 2

    # 绘制左侧矩形
    for y in range(height):
        for x in range(int(center_x)):
            date[x, y] = color

    # 绘制右侧矩形
    if color2 != None:
        for y in range(height):
            for x in range(int(center_x), width):
                date[x, y] = color2

    return date

# Rotate image and crop
def rotate_and_crop(image_array, angle, output_size=(8, 4)):
    """旋转16*16色盘并提取中间8*4区域"""
    orig_height, orig_width = image_array.shape[:2]
    out_width, out_height = output_size
    
    # 创建PIL图像
    image = Image.fromarray(image_array)
    
    # 计算中心点
    center = (orig_width/2, orig_height/2)
    
    # 旋转图像
    rotated_image = image.rotate(
        angle, 
        resample=Image.BICUBIC,
        center=center,
        expand=False
    )
    
    # 计算要提取的中间区域
    left = (orig_width - out_width) // 2
    top = (orig_height - out_height) // 2
    right = left + out_width
    bottom = top + out_height
    
    # 提取中间区域
    cropped_image = rotated_image.crop((left, top, right, bottom))
    
    return np.array(cropped_image)

_matrix = []

def spin(rgb_matrix, config, single=True):
    global frame_index, _matrix

    if _matrix == []:
        color = tuple(config.get('rgb_matrix_color', DEFAULT_COLOR)) or DEFAULT_COLOR
        if single:
            _matrix = draw_2_half_rectangle_matrix(color=color)
        else:
            color2 = tuple(config.get('rgb_matrix_color2', DEFAULT_COLOR2)) or DEFAULT_COLOR2
            _matrix = draw_2_half_rectangle_matrix(color=color, color2=color2)

    speed = config['rgb_matrix_speed']
    interval = 1 / speed

    angle = frame_index * (360 / MAX_FRAME)
    frame_index += 1
    if frame_index >= MAX_FRAME:
        frame_index = 0
    rotated_matrix = rotate_and_crop(_matrix, angle)
    rotated_matrix = rotated_matrix.tolist()
    for y in range(8):
        for x in range(4):
            r = rotated_matrix[x][y][0]
            g = rotated_matrix[x][y][1]
            b = rotated_matrix[x][y][2]
            rgb_matrix.draw_point((y, x), (r, g, b))
    rgb_matrix.display()
    time.sleep(interval)

def dual_spin(rgb_matrix, config):
    spin(rgb_matrix, config, single=False)

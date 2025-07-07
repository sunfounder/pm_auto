import numpy as np
import time

MAX_FRAME = 36
DEFAULT_COLOR = (255, 165, 0)
frame_index = 0

# 生成带两个对称中心边矩形的8x4 RGB矩阵
def generate_rectangle_matrix(color=(255, 0, 0), color2=None):
    matrix = np.zeros((8, 4, 3), dtype=np.uint8)
    
    left1 = 0
    right1 = 3
    top1 = 0
    bottom1 = 3
    
    left2 = 0
    right2 = 3
    top2 = 4
    bottom2 = 7
    
    # 填充左侧矩形区域
    for y in range(top1, bottom1 + 1):
        for x in range(left1, right1 + 1):
            matrix[y, x] = color  # 左侧矩形颜色
    
    if color2 != None:
        # 填充右侧矩形区域
        for y in range(top2, bottom2 + 1):
            for x in range(left2, right2 + 1):
                matrix[y, x] = color2  # 右侧矩形颜色
    
    return matrix

# 旋转RGB矩阵 - 支持任意角度和矩阵尺寸
def rotate_matrix(matrix, angle_degrees, center=None, use_bilinear=True):
    height, width = matrix.shape[:2]
    
    # 如果未指定中心，则使用矩阵中心
    if center is None:
        center_y, center_x = (height - 1) / 2, (width - 1) / 2
    else:
        center_x, center_y = center
    
    angle_radians = np.radians(angle_degrees)
    cos_val = np.cos(angle_radians)
    sin_val = np.sin(angle_radians)
    
    rotated = np.zeros_like(matrix)
    
    for y in range(height):
        for x in range(width):
            offset_x = x - center_x
            offset_y = y - center_y
            
            src_x = center_x + offset_x * cos_val + offset_y * sin_val
            src_y = center_y - offset_x * sin_val + offset_y * cos_val
            
            if use_bilinear:
                x1, y1 = int(src_x), int(src_y)
                x2, y2 = x1 + 1, y1 + 1
                
                if 0 <= x1 < width and 0 <= x2 < width and 0 <= y1 < height and 0 <= y2 < height:
                    fx = src_x - x1
                    fy = src_y - y1
                    
                    for c in range(3):
                        value = (1-fx)*(1-fy)*matrix[y1, x1, c] + \
                                fx*(1-fy)*matrix[y1, x2, c] + \
                                (1-fx)*fy*matrix[y2, x1, c] + \
                                fx*fy*matrix[y2, x2, c]
                        value = max(0, min(255, int(value)))
                        rotated[y, x, c] = value
            else:
                src_x_int, src_y_int = int(round(src_x)), int(round(src_y))
                if 0 <= src_x_int < width and 0 <= src_y_int < height:
                    rotated[y, x] = matrix[src_y_int, src_x_int]
    
    return rotated

_matrix = []

def spin(rgb_matrix, config):
    global frame_index, _matrix

    color = tuple(config.get('rgb_matrix_color', DEFAULT_COLOR)) or DEFAULT_COLOR
    if _matrix == []:
        _matrix = generate_rectangle_matrix(color)

    speed = config['rgb_matrix_speed']
    interval = 1 / speed

    angle = frame_index * (360 / MAX_FRAME)
    frame_index += 1
    if frame_index >= MAX_FRAME:
        frame_index = 0
    rotated_matrix = rotate_matrix(_matrix, angle)
    rotated_matrix = rotated_matrix.tolist()
    # print(rotated_matrix)
    # print('--------------------------------------')
    for x in range(8):
        for y in range(4):
            r = rotated_matrix[x][y][0]
            g = rotated_matrix[x][y][1]
            b = rotated_matrix[x][y][2]
            rgb_matrix.draw_point((x, y), (r, g, b))
    rgb_matrix.display()
    time.sleep(interval)

import numpy as np
import time

MAX_FRAME = 36
frame_index = 0

# 生成带两个对称中心边矩形的8x4 RGB矩阵
def generate_rectangle_matrix(color1=(255, 0, 0), color2=(0, 0, 255)):
    matrix = np.zeros((8, 4, 3), dtype=np.uint8)
    
    # 矩形参数 - 宽度为2，高度为4，底部边的中点在矩阵中心两侧
    rect_width = 2
    rect_height = 4
    center_x1, center_y1 = 0.5, 3.5  # 左侧矩形物理中心
    center_x2, center_y2 = 2.5, 3.5  # 右侧矩形物理中心
    
    # 计算左侧矩形四个顶点坐标
    left1 = int(max(0, center_x1 - rect_width / 2 + 0.5))
    right1 = int(min(3, center_x1 + rect_width / 2 - 0.5))
    top1 = int(max(0, center_y1 - rect_height + 1))
    bottom1 = int(center_y1)
    
    # 计算右侧矩形四个顶点坐标
    left2 = int(max(0, center_x2 - rect_width / 2 + 0.5))
    right2 = int(min(3, center_x2 + rect_width / 2 - 0.5))
    top2 = int(max(0, center_y2 - rect_height + 1))
    bottom2 = int(center_y2)
    
    # 填充左侧矩形区域
    for y in range(top1, bottom1 + 1):
        for x in range(left1, right1 + 1):
            matrix[y, x] = color1  # 左侧矩形颜色
    
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

_matrix = generate_rectangle_matrix(color1=(255, 0, 0), color2=(0, 0, 255))

def roate_dual(rgb_matrix, config):
    global frame_index

    speed = config['rgb_matrix_speed']
    interval = 1 / speed

    angle = frame_index * (360 / MAX_FRAME)
    frame_index += 1
    if frame_index >= MAX_FRAME:
        frame_index = 0

    
    # 左侧矩形顺时针旋转
    left_rotated = rotate_matrix(_matrix, angle, center=(0.5, 3.5))
    
    # 右侧矩形逆时针旋转（相对于左侧矩形对称）
    right_rotated = rotate_matrix(_matrix, angle+180, center=(2.5, 3.5))
    
    # 合并两个旋转结果
    final_matrix = np.zeros_like(_matrix)
    
    # 左侧区域使用左矩形旋转结果
    for y in range(8):
        for x in range(2):
            final_matrix[y, x] = left_rotated[y, x]
    
    # 右侧区域使用右矩形旋转结果
    for y in range(8):
        for x in range(2, 4):
            final_matrix[y, x] = right_rotated[y, x]
    
    final_matrix = final_matrix.tolist()
    for x in range(8):
        for y in range(4):
            r = final_matrix[x][y][0]
            g = final_matrix[x][y][1]
            b = final_matrix[x][y][2]
            rgb_matrix.draw_point((x, y), (r, g, b))
    rgb_matrix.display()
    time.sleep(interval)


import colorsys
import time
from .spin import rotate_matrix, generate_rectangle_matrix

MAX_FRAME = 36
frame_index = 0

# 主函数
def shift_spin(rgb_matrix, config):
    global frame_index

    speed = config['rgb_matrix_speed']
    interval = 1 / speed

    angle = frame_index * (360 / MAX_FRAME)
    # 根据帧索引计算HSV颜色
    hue = frame_index / MAX_FRAME
    saturation = 1.0
    value = 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    color = (r, g, b)
    _matrix = generate_rectangle_matrix(color=color)
    frame_index += 1
    if frame_index >= MAX_FRAME:
        frame_index = 0
    rotated_matrix = rotate_matrix(_matrix, angle)
    rotated_matrix = rotated_matrix.tolist()
    for x in range(8):
        for y in range(4):
            r = rotated_matrix[x][y][0]
            g = rotated_matrix[x][y][1]
            b = rotated_matrix[x][y][2]
            rgb_matrix.draw_point((x, y), (r, g, b))
    rgb_matrix.display()
    time.sleep(interval)

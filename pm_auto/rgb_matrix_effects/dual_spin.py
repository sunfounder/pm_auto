import numpy as np
import time
from .spin import rotate_matrix, generate_rectangle_matrix

MAX_FRAME = 36
DEFAULT_COLOR_1 = (255, 0, 0)
DEFAULT_COLOR_2 = (0, 0, 255)
frame_index = 0

_matrix = []

def dual_spin(rgb_matrix, config):
    global frame_index, _matrix

    if _matrix == []:
        color1 = tuple(config.get('rgb_matrix_color', DEFAULT_COLOR_1)) or DEFAULT_COLOR_1
        color2 = tuple(config.get('rgb_matrix_color2', DEFAULT_COLOR_2)) or DEFAULT_COLOR_2
        _matrix = generate_rectangle_matrix(color1, color2)

    speed = config['rgb_matrix_speed']
    interval = 1 / speed

    angle = frame_index * (360 / MAX_FRAME)
    frame_index += 1
    if frame_index >= MAX_FRAME:
        frame_index = 0

    final_matrix = rotate_matrix(_matrix, angle, center=(1.5, 3.5))
    
    final_matrix = final_matrix.tolist()
    for x in range(8):
        for y in range(4):
            r = final_matrix[x][y][0]
            g = final_matrix[x][y][1]
            b = final_matrix[x][y][2]
            rgb_matrix.draw_point((x, y), (r, g, b))
    rgb_matrix.display()
    time.sleep(interval)


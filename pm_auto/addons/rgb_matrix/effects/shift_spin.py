import colorsys
import time
from .spin import draw_2_half_rectangle_matrix, rotate_and_crop
from pm_auto.libs.color import Color

MAX_FRAME = 36
DEFAULT_COLOR = (255, 0, 0)
frame_index = 0

# 主函数
def shift_spin(self, rgb_matrix):
    global frame_index

    speed = self.speed
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
    color = Color.apply_brightness((r, g, b), self.brightness)
    _matrix = draw_2_half_rectangle_matrix(color=color)
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

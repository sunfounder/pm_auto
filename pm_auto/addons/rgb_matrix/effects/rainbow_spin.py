import numpy as np
from .spin import rotate_and_crop
import time
from pm_auto.libs.color import Color

MAX_FRAME = 40
frame_index = 0

def hsv_to_rgb(hsv):
    """
    Convert HSV values to RGB.

    Parameters
    ----------
    hsv : (..., 3) array-like
       All values assumed to be in range [0, 1]

    Returns
    -------
    (..., 3) `~numpy.ndarray`
       Colors converted to RGB values in range [0, 1]
    """
    hsv = np.asarray(hsv)

    # check length of the last dimension, should be _some_ sort of rgb
    if hsv.shape[-1] != 3:
        raise ValueError("Last dimension of input array must be 3; "
                         f"shape {hsv.shape} was found.")

    in_shape = hsv.shape
    hsv = np.array(
        hsv, copy=False,
        dtype=np.promote_types(hsv.dtype, np.float32),  # Don't work on ints.
        ndmin=2,  # In case input was 1D.
    )

    h = hsv[..., 0]
    s = hsv[..., 1]
    v = hsv[..., 2]

    r = np.empty_like(h)
    g = np.empty_like(h)
    b = np.empty_like(h)

    i = (h * 6.0).astype(int)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))

    idx = i % 6 == 0
    r[idx] = v[idx]
    g[idx] = t[idx]
    b[idx] = p[idx]

    idx = i == 1
    r[idx] = q[idx]
    g[idx] = v[idx]
    b[idx] = p[idx]

    idx = i == 2
    r[idx] = p[idx]
    g[idx] = v[idx]
    b[idx] = t[idx]

    idx = i == 3
    r[idx] = p[idx]
    g[idx] = q[idx]
    b[idx] = v[idx]

    idx = i == 4
    r[idx] = t[idx]
    g[idx] = p[idx]
    b[idx] = v[idx]

    idx = i == 5
    r[idx] = v[idx]
    g[idx] = p[idx]
    b[idx] = q[idx]

    idx = s == 0
    r[idx] = v[idx]
    g[idx] = v[idx]
    b[idx] = v[idx]

    rgb = np.stack([r, g, b], axis=-1)

    return rgb.reshape(in_shape)

def create_hsv_wheel(width=16, height=16):
    """创建仅包含 7 种颜色的 HSV 色盘（以图像中心为原点）"""
    y, x = np.mgrid[0:height, 0:width]
    center_x, center_y = (width - 1) / 2, (height - 1) / 2
    dx, dy = x - center_x, y - center_y

    theta = np.arctan2(dy, dx)  # 弧度 [-π, π]

    # 将角度离散化为 7 个值
    num_colors = 7
    discrete_theta = np.round(theta / (2 * np.pi) * num_colors) % num_colors
    h = discrete_theta / num_colors  # [0, 1] 范围，仅 7 个不同值

    # 固定饱和度和明度为 1，避免渐变
    s = np.ones_like(h)
    v = np.ones_like(h)

    hsv = np.stack([h, s, v], axis=2)
    rgb = hsv_to_rgb(hsv)
    return (rgb * 255).astype(np.uint8)

hsv_wheel_16_16 = create_hsv_wheel(16, 16)

def rainbow_spin(self, rgb_matrix):
    global frame_index

    speed = self.speed
    interval = 1 / speed

    angle = frame_index * (360 / MAX_FRAME)

    rotated_cropped_8_4 = rotate_and_crop(hsv_wheel_16_16, angle)

    frame_index += 1
    if frame_index >= MAX_FRAME:
        frame_index = 0

    rotated_cropped_8_4 = np.array(rotated_cropped_8_4).tolist()
    for y in range(8):
        for x in range(4):
            r = rotated_cropped_8_4[x][y][0]
            g = rotated_cropped_8_4[x][y][1]
            b = rotated_cropped_8_4[x][y][2]
            color = Color.apply_brightness((r, g, b), self.brightness)
            rgb_matrix.draw_point((y, x), color)
    rgb_matrix.display()
    time.sleep(interval)
    

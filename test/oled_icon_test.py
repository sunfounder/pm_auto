'''
This is a test icon display to adjust the threshold when converting to binary pixels.

Can run on Windows.
Need to install dependencies:

    pip3 install pillow matplotlib numpy

'''

import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

WIDTH = 128
HEIGHT = 64

image = Image.new('1', (WIDTH, HEIGHT))
# image = np.ones((WIDTH, HEIGHT, 3), dtype=np.float32)
ICONS_PATH = '/pm_auto/icons'


current_dir = Path(__file__).resolve().parent
working_dir = os.path.join(str(current_dir.parent) + ICONS_PATH)
print(f'Working directory: {working_dir}')
os.chdir(working_dir)


def draw_icon(icon, x, y, scale=1.0, invert=False,  dither=True, threshold=127):
    img = Image.open(icon)

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 缩放
    if scale != 1.0:
        print("scale", scale)
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 处理透明背景
    r, g, b, a = img.split()
    white = Image.new('L', img.size, 255)
    converted_img = Image.merge('RGBA', (white, white, white, a))
    background = Image.new('RGBA', img.size, (0, 0, 0, 255))
    final_img = Image.alpha_composite(background, converted_img)

    if not dither:
        # 直接阈值法（无抖动）
        final_img = final_img.convert('L')  # 转换为灰度图
        final_img = final_img.point(lambda p: 255 if p > threshold else 0)
    else:
        # 抖动算法（生成更平滑的黑白效果）
        final_img = final_img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)

    # 反转
    if invert:
            final_img = Image.eval(final_img, lambda x: 255 - x)

    # 绘制到画布上
    image.paste(final_img, (x, y), None)


# fig, ax = plt.subplots(figsize=(128/10, 64/10), constrained_layout=True)
fig, ax = plt.subplots(figsize=(128/20, 64/20), constrained_layout=True)

ax.grid(True, which='both', color='gray', linestyle='-', linewidth=0.5, alpha=1)
ax.set_xticks(np.arange(-0.5, WIDTH, 1))
ax.set_yticks(np.arange(-0.5, HEIGHT, 1))
ax.set_xticklabels(np.arange(0, WIDTH+1, 1), rotation=90, ha='right', fontsize=8)
ax.set_yticklabels(np.arange(0, HEIGHT+1, 1), rotation=0, ha='right', fontsize=8)

# draw_icon('../icons/fan_icon_24.png', 0, 0, scale=1.0, invert=False, dither=False)
# draw_icon('../icons/fan_icon_24.png', 30, 0, scale=1.0, invert=False, dither=True)

# draw_icon('../icons/temperature_icon_24.png', 0, 30, scale=1.0, invert=False, dither=False, threshold=158)
# draw_icon('../icons/temperature_icon_24.png', 30, 30, scale=1.0, invert=False, dither=True)

# draw_icon('../icons/raid_icon_20.png', 0, 0, scale=1.0, invert=False, dither=False, threshold=200)
# draw_icon('../icons/raid_icon_20.png', 30, 0, scale=1.0, invert=False, dither=True)

# draw_icon('../icons/ram_icon_24.png', 0, 30, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/ram_icon_24.png', 30, 30, scale=1.0, invert=False, dither=True)

# draw_icon('../icons/wifi_icon_20.png', 0, 30, scale=1.0, invert=False, dither=False, threshold=85)
# draw_icon('../icons/wifi_icon_20.png', 30, 30, scale=1.0, invert=False, dither=True)

# draw_icon('../icons/net_icon_20.png', 30, 30, scale=1.0, invert=False, dither=True)
# draw_icon('../icons/net_icon_20.png', 0, 0, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/net_icon_20.png', 25, 0, scale=1.0, invert=False, dither=False, threshold=10)
# draw_icon('../icons/net_icon_20.png', 50, 0, scale=1.0, invert=False, dither=False, threshold=50)
# draw_icon('../icons/net_icon_20.png', 75, 0, scale=1.0, invert=False, dither=False, threshold=80)
# draw_icon('../icons/net_icon_20.png', 100, 0, scale=1.0, invert=False, dither=False, threshold=100)

# draw_icon('../icons/ethernet_icon_20.png', 30, 30, scale=1.0, invert=False, dither=True)
# draw_icon('../icons/ethernet_icon_20.png', 0, 0, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/ethernet_icon_20.png', 25, 0, scale=1.0, invert=False, dither=False, threshold=10)
# draw_icon('../icons/ethernet_icon_20.png', 50, 0, scale=1.0, invert=False, dither=False, threshold=50)
# draw_icon('../icons/ethernet_icon_20.png', 75, 0, scale=1.0, invert=False, dither=False, threshold=80)
# draw_icon('../icons/ethernet_icon_20.png', 100, 0, scale=1.0, invert=False, dither=False, threshold=100)

# draw_icon('../icons/sdcard_icon_20.png', 0, 0, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/sdcard_icon_20.png', 25, 0, scale=1.0, invert=False, dither=False, threshold=10)
# draw_icon('../icons/sdcard_icon_20.png', 50, 0, scale=1.0, invert=False, dither=False, threshold=50)
# draw_icon('../icons/sdcard_icon_20.png', 75, 0, scale=1.0, invert=False, dither=False, threshold=80)
# draw_icon('../icons/sdcard_icon_20.png', 100, 0, scale=1.0, invert=False, dither=False, threshold=100)
# draw_icon('../icons/sdcard_icon_20.png', 0, 30, scale=1.0, invert=False, dither=True)
# draw_icon('../icons/sdcard_icon_20.png', 25, 30, scale=1.0, invert=False, dither=False, threshold=130)
# draw_icon('../icons/sdcard_icon_20.png', 50, 30, scale=1.0, invert=False, dither=False, threshold=150)
# draw_icon('../icons/sdcard_icon_20.png', 75, 30, scale=1.0, invert=False, dither=False, threshold=180)
# draw_icon('../icons/sdcard_icon_20.png', 100, 30, scale=1.0, invert=False, dither=False, threshold=210)

# draw_icon('../icons/nvme_icon_20.png', 0, 0, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/nvme_icon_20.png', 25, 0, scale=1.0, invert=False, dither=False, threshold=10)
# draw_icon('../icons/nvme_icon_20.png', 50, 0, scale=1.0, invert=False, dither=False, threshold=50)
# draw_icon('../icons/nvme_icon_20.png', 75, 0, scale=1.0, invert=False, dither=False, threshold=80)
# draw_icon('../icons/nvme_icon_20.png', 100, 0, scale=1.0, invert=False, dither=False, threshold=100)
# draw_icon('../icons/nvme_icon_20.png', 0, 30, scale=1.0, invert=False, dither=True)
# draw_icon('../icons/nvme_icon_20.png', 25, 30, scale=1.0, invert=False, dither=False, threshold=130)
# draw_icon('../icons/nvme_icon_20.png', 50, 30, scale=1.0, invert=False, dither=False, threshold=150)
# draw_icon('../icons/nvme_icon_20.png', 75, 30, scale=1.0, invert=False, dither=False, threshold=180)
# draw_icon('../icons/nvme_icon_20.png', 100, 30, scale=1.0, invert=False, dither=False, threshold=210)

# draw_icon('../icons/usb_stick_icon_20.png', 0, 3, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/usb_stick_icon_20.png', 25, 3, scale=1.0, invert=False, dither=False, threshold=10)
# draw_icon('../icons/usb_stick_icon_20.png', 50, 3, scale=1.0, invert=False, dither=False, threshold=50)
# draw_icon('../icons/usb_stick_icon_20.png', 75, 3, scale=1.0, invert=False, dither=False, threshold=80)
# draw_icon('../icons/usb_stick_icon_20.png', 100, 3, scale=1.0, invert=False, dither=False, threshold=100)
# draw_icon('../icons/usb_stick_icon_20.png', 0, 30, scale=1.0, invert=False, dither=True)
# draw_icon('../icons/usb_stick_icon_20.png', 25, 30, scale=1.0, invert=False, dither=False, threshold=130)
# draw_icon('../icons/usb_stick_icon_20.png', 50, 30, scale=1.0, invert=False, dither=False, threshold=150)
# draw_icon('../icons/usb_stick_icon_20.png', 75, 30, scale=1.0, invert=False, dither=False, threshold=180)
# draw_icon('../icons/usb_stick_icon_20.png', 100, 30, scale=1.0, invert=False, dither=False, threshold=210)

# draw_icon('../icons/raid_icon_20.png', 0, 3, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/raid_icon_20.png', 25, 3, scale=1.0, invert=False, dither=False, threshold=10)
# draw_icon('../icons/raid_icon_20.png', 50, 3, scale=1.0, invert=False, dither=False, threshold=50)
# draw_icon('../icons/raid_icon_20.png', 75, 3, scale=1.0, invert=False, dither=False, threshold=80)
# draw_icon('../icons/raid_icon_20.png', 100, 3, scale=1.0, invert=False, dither=False, threshold=100)
# draw_icon('../icons/raid_icon_20.png', 0, 30, scale=1.0, invert=False, dither=True)
# draw_icon('../icons/raid_icon_20.png', 25, 30, scale=1.0, invert=False, dither=False, threshold=130)
# draw_icon('../icons/raid_icon_20.png', 50, 30, scale=1.0, invert=False, dither=False, threshold=150)
# draw_icon('../icons/raid_icon_20.png', 75, 30, scale=1.0, invert=False, dither=False, threshold=180)
# draw_icon('../icons/raid_icon_20.png', 100, 30, scale=1.0, invert=False, dither=False, threshold=210)

# draw_icon('../icons/charge_icon_20.png', 0, 3, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/charge_icon_20.png', 25, 3, scale=1.0, invert=False, dither=False, threshold=10)
# draw_icon('../icons/charge_icon_20.png', 50, 3, scale=1.0, invert=False, dither=False, threshold=50)
# draw_icon('../icons/charge_icon_20.png', 75, 3, scale=1.0, invert=False, dither=False, threshold=80)
# draw_icon('../icons/charge_icon_20.png', 100, 3, scale=1.0, invert=False, dither=False, threshold=100)
# draw_icon('../icons/charge_icon_20.png', 0, 30, scale=1.0, invert=False, dither=True)
# draw_icon('../icons/charge_icon_20.png', 25, 30, scale=1.0, invert=False, dither=False, threshold=130)
# draw_icon('../icons/charge_icon_20.png', 50, 30, scale=1.0, invert=False, dither=False, threshold=150)
# draw_icon('../icons/charge_icon_20.png', 75, 30, scale=1.0, invert=False, dither=False, threshold=180)
# draw_icon('../icons/charge_icon_20.png', 100, 30, scale=1.0, invert=False, dither=False, threshold=210)

# draw_icon('../icons/battery_icon_40.png', 0, 3, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/battery_icon_40.png', 45, 3, scale=1.0, invert=False, dither=False, threshold=10)
# draw_icon('../icons/battery_icon_40.png', 90, 3, scale=1.0, invert=False, dither=False, threshold=220)
# draw_icon('../icons/battery_icon_40.png', 0, 3, scale=1.0, invert=False, dither=True)
# draw_icon('../icons/battery_icon_40.png', 45, 3, scale=1.0, invert=False, dither=False, threshold=80)
# draw_icon('../icons/battery_icon_40.png', 90, 3, scale=1.0, invert=False, dither=False, threshold=100)
# draw_icon('../icons/battery_icon_40.png', 0, 3, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/battery_icon_40.png', 45, 3, scale=1.0, invert=False, dither=False, threshold=130)
# draw_icon('../icons/battery_icon_40.png', 90, 3, scale=1.0, invert=False, dither=False, threshold=180)

# draw_icon('../icons/cable_plug_icon_48.png', 0, 3, scale=1.0, invert=False, dither=False, threshold=127)
# draw_icon('../icons/cable_plug_icon_48.png', 50, 3, scale=1.0, invert=False, dither=True)

# draw_icon('../icons/raspberry_icon_48.png', 0, 0, scale=1.0, invert=False, dither=False, threshold=130)
# draw_icon('../icons/raspberry_icon_48.png', 50, 3, scale=1.0, invert=False, dither=True)

draw_icon('sunfounder.ico', 0, 3, scale=1.0, invert=False, dither=False, threshold=127)
draw_icon('sunfounder.ico', 25, 3, scale=1.0, invert=False, dither=False, threshold=10)
draw_icon('sunfounder.ico', 50, 3, scale=1.0, invert=False, dither=False, threshold=50)
draw_icon('sunfounder.ico', 75, 3, scale=1.0, invert=False, dither=False, threshold=80)
draw_icon('sunfounder.ico', 100, 3, scale=1.0, invert=False, dither=False, threshold=100)
draw_icon('sunfounder.ico', 0, 30, scale=1.0, invert=False, dither=True)
draw_icon('sunfounder.ico', 25, 30, scale=1.0, invert=False, dither=False, threshold=130)
draw_icon('sunfounder.ico', 50, 30, scale=1.0, invert=False, dither=False, threshold=150)
draw_icon('sunfounder.ico', 75, 30, scale=1.0, invert=False, dither=False, threshold=180)
draw_icon('sunfounder.ico', 100, 30, scale=1.0, invert=False, dither=False, threshold=210)

# ax.imshow(np.array(image), cmap='gray_r', aspect='equal')
ax.imshow(np.array(image), cmap='Blues_r', aspect='auto')


plt.show()
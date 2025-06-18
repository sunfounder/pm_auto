import time

rectangle_coor = [0, 0, 7, 3]
frame_index = 0

def breathing(rgb_matrix, color=(255, 255, 255), interval=0.05):
    global frame_index
    max_frames = 200
    r, g, b = color

    if frame_index < 100:
        r = int(r * frame_index / 100)
        g = int(g * frame_index / 100)
        b = int(b * frame_index / 100)
    else:
        r = int(r * (200 - frame_index) / 100)
        g = int(g * (200 - frame_index) / 100)
        b = int(b * (200 - frame_index) / 100)

    frame_index += 1
    if frame_index > max_frames:
        frame_index = 0

    rgb_matrix.draw_rectangle(rectangle_coor, fill=(r, g, b), outline=None, width=0)
    rgb_matrix.display()
    time.sleep(interval)
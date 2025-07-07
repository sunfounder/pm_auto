from ..libs.color import Color

firsthue = 0

list = [[0, 0, 0, 7], 
        [1, 0, 1, 7], 
        [2, 0, 2, 7], 
        [3, 0, 3, 7],
        [4, 0, 4, 7], 
        [5, 0, 5, 7], 
        [6, 0, 6, 7], 
        [7, 0, 7, 7]]

def rainbow(rgb_matrix, config, reverse=False):
    global firsthue, list

    if reverse:
        list.reverse()

    j = 0
    for i in list:
        hue = firsthue + j * 95
        j = j + 1
        if hue > 1530:
            hue = hue - 1530
        temp = Color.hsv_to_rgb(hue)
        rgb_matrix.draw_line(i, (temp[0], temp[1], temp[2]))

    rgb_matrix.display()

    firsthue = firsthue + 11
    if firsthue > 1530:
        firsthue = 0

def rainbow_reverse(rgb_matrix, config):
    rainbow(rgb_matrix, config, reverse=True)

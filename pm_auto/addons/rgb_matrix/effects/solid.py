rectangle_coor = [0, 0, 7, 3]

def solid(rgb_matrix, config):
    color = tuple(config['rgb_matrix_color'])
    rgb_matrix.draw_rectangle(rectangle_coor,
                              fill=color,
                              outline=None, width=0)
    rgb_matrix.display()
rectangle_coor = [0, 0, 7, 3]

def solid(self, rgb_matrix):
    color = tuple(self.color)
    rgb_matrix.draw_rectangle(rectangle_coor,
                              fill=color,
                              outline=None, width=0)
    rgb_matrix.display()
from libs.color import Color

RECTANGLE_COORD = [0, 0, 7, 3]

def solid(self, rgb_matrix):
    color = Color.apply_brightness(self.color, self.brightness)
    rgb_matrix.draw_rectangle(RECTANGLE_COORD,
                              fill=color,
                              outline=None, width=0)
    rgb_matrix.display()
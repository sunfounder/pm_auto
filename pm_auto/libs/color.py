import random

def constrain(x, low, high):
    return min(max(x, low), high)
    
class Color():
    def color(self, value):
        if self.iscolor(value):
            return value
        else:
            self.raise_not_color(value)
    def led_color(self, value):
        if self.iscolor(value):
            return value
        else:
            self.raise_not_color(value)

    def iscolor(self, value):
        if not isinstance(value, str):
            return False
        if not value.startswith("#"):
            return False
        color = value[1:]
        if len(color) == 6:
            try:
                int(color,16)
                return True
            except:
                return False
        else:
            return False

    def raise_not_color(self, value):
        raise ValueError('Color must be in form of "#ff45b6", not {}({})'.format(value, type(value)))

    def get_from(self, rgb, c):
        if not self.iscolor(c):
            self.raise_not_color(c)
        rgb = rgb.lower()
        if rgb == 'red':
            return int(c[1:3], 16)
        elif rgb == 'green':
            return int(c[3:5], 16)
        elif rgb == 'blue':
            return int(c[5:7], 16)
        else:
            raise ValueError('RGB value must be "red", "green" or "blue", not {}({})'.format(rgb, type(rgb)))

    def random(self):
        return '#{:06X}'.format(random.randint(0, 2**24 - 1))
    
    def colorful(self,x):
        return '#{:06X}'.format(x)
	
    def rgb(self, r,g,b):
        r = int(constrain(r, 0, 255))
        g = int(constrain(g, 0, 255))
        b = int(constrain(b, 0, 255))
        return '#{:02X}{:02X}{:02X}'.format(r, g, b)

    def blend(self, colour1, colour2, ratio):
        if not self.iscolor(colour1):
            self.raise_not_color(colour1)
        if not self.iscolor(colour2):
            self.raise_not_color(colour1)
        r1, r2 = int(colour1[1:3], 16), int(colour2[1:3], 16)
        g1, g2 = int(colour1[3:5], 16), int(colour2[3:5], 16)
        b1, b2 = int(colour1[5:7], 16), int(colour2[5:7], 16)
        ratio = min(1, max(0, ratio))
        r = round(r1 * (1 - ratio) + r2 * ratio)
        g = round(g1 * (1 - ratio) + g2 * ratio)
        b = round(b1 * (1 - ratio) + b2 * ratio)
        return '#{:02X}{:02X}{:02X}'.format(r, g, b)

    @staticmethod
    def apply_brightness(color, brightness):
        r, g, b = color
        r = int(r * brightness / 100)
        g = int(g * brightness / 100)
        b = int(b * brightness / 100)
        return (r, g, b)

    # str or hex, eg: 'ffffff', '#ffffff', '#FFFFFF'
    @staticmethod
    def hex_to_rgb(hex):
        hex = hex.strip().replace('#', '')
        r = int(hex[0:2], 16)
        g = int(hex[2:4], 16)
        b = int(hex[4:6], 16)
        return [r, g, b]


    @staticmethod
    def hsl_to_rgb(hue, saturation=1, brightness=1):
        hue = hue % 360
        _hi = int((hue/60)%6)
        _f = hue / 60.0 - _hi
        _p = brightness * (1 - saturation)
        _q = brightness * (1 - _f * saturation)
        _t = brightness * (1 - (1 - _f) * saturation)
        
        if _hi == 0:
            _R_val = brightness
            _G_val = _t
            _B_val = _p
        if _hi == 1:
            _R_val = _q
            _G_val = brightness
            _B_val = _p
        if _hi == 2:
            _R_val = _p
            _G_val = brightness
            _B_val = _t
        if _hi == 3:
            _R_val = _p
            _G_val = _q
            _B_val = brightness
        if _hi == 4:
            _R_val = _t
            _G_val = _p
            _B_val = brightness
        if _hi == 5:
            _R_val = brightness
            _G_val = _p
            _B_val = _q
        
        r = int(_R_val * 255)
        g = int(_G_val * 255)
        b = int(_B_val * 255)
        return (r, g, b)
    
    @staticmethod
    def hsv_to_rgb(hue):
        if hue < 510:  # Red to Green-1
            b = 0
            if hue < 255:  #   Red to Yellow-1
                r = 255
                g = hue  #     g = 0 to 254
            else:  #   Yellow to Green-1
                r = 510 - hue  #     r = 255 to 1
                g = 255

        elif hue < 1020:  # Green to Blue-1
            r = 0
            if hue < 765:  #   Green to Cyan-1
                g = 255
                b = hue - 510  #     b = 0 to 254
            else:  #   Cyan to Blue-1
                g = 1020 - hue  #     g = 255 to 1
                b = 255

        elif hue < 1530:  # Blue to Red-1
            g = 0
            if hue < 1275:  #   Blue to Magenta-1
                r = hue - 1020  #     r = 0 to 254
                b = 255
            else:  #   Magenta to Red-1
                r = 255
                b = 1530 - hue  #     b = 255 to 1

        else:  # Last 0.5 Red (quicker than % operator)
            r = 255
            g = b = 0

        list = [r, g, b]
        return list
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from __future__ import division
from PIL import Image, ImageDraw, ImageFont
from importlib.resources import files as resource_files

from .i2c import I2C
from .utils import run_command

__package_name__ = __name__.split('.')[0]

# Constants
SSD1306_I2C_ADDRESS_1 = 0x3C
SSD1306_I2C_ADDRESS_2 = 0x3D
SSD1306_SETCONTRAST = 0x81
SSD1306_DISPLAYALLON_RESUME = 0xA4
SSD1306_DISPLAYALLON = 0xA5
SSD1306_NORMALDISPLAY = 0xA6
SSD1306_INVERTDISPLAY = 0xA7
SSD1306_DISPLAYOFF = 0xAE
SSD1306_DISPLAYON = 0xAF
SSD1306_SETDISPLAYOFFSET = 0xD3
SSD1306_SETCOMPINS = 0xDA
SSD1306_SETVCOMDETECT = 0xDB
SSD1306_SETDISPLAYCLOCKDIV = 0xD5
SSD1306_SETPRECHARGE = 0xD9
SSD1306_SETMULTIPLEX = 0xA8
SSD1306_SETLOWCOLUMN = 0x00
SSD1306_SETHIGHCOLUMN = 0x10
SSD1306_SETSTARTLINE = 0x40
SSD1306_MEMORYMODE = 0x20
SSD1306_COLUMNADDR = 0x21
SSD1306_PAGEADDR = 0x22
SSD1306_COMSCANINC = 0xC0
SSD1306_COMSCANDEC = 0xC8
SSD1306_SEGREMAP = 0xA0
SSD1306_CHARGEPUMP = 0x8D
SSD1306_EXTERNALVCC = 0x1
SSD1306_SWITCHCAPVCC = 0x2

# Scrolling constants
SSD1306_ACTIVATE_SCROLL = 0x2F
SSD1306_DEACTIVATE_SCROLL = 0x2E
SSD1306_SET_VERTICAL_SCROLL_AREA = 0xA3
SSD1306_RIGHT_HORIZONTAL_SCROLL = 0x26
SSD1306_LEFT_HORIZONTAL_SCROLL = 0x27
SSD1306_VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL = 0x29
SSD1306_VERTICAL_AND_LEFT_HORIZONTAL_SCROLL = 0x2A


class SSD1306Base(object):
    """Base class for SSD1306-based OLED displays.  Implementors should subclass
    and provide an implementation for the _initialize function.
    """

    def __init__(self, width, height, i2c_bus=None, address=SSD1306_I2C_ADDRESS_1, i2c=None):

        self._i2c = I2C(address)
        self.width = width
        self.height = height
        self._pages = height//8
        self._buffer = [0]*(width*self._pages)

    def _initialize(self):
        raise NotImplementedError

    def write_command(self, c):
        """Send write_command byte to display."""
        # I2C write.
        control = 0x00   # Co = 0, DC = 0
        self._i2c.write_byte_data(control, c)

    def write_data(self, c):
        """Send byte of data to display."""
        # I2C write.
        control = 0x40   # Co = 0, DC = 0
        self._i2c.write_byte_data(control, c)

    def begin(self, vccstate=SSD1306_SWITCHCAPVCC):
        """Initialize display."""
        # Save vcc state.
        self._vccstate = vccstate
        # Reset and initialize display.
        self._initialize()
        # Turn on the display.
        self.on()


    def on(self):
        self.write_command(SSD1306_DISPLAYON)

    def off(self):
        self.write_command(SSD1306_DISPLAYOFF)

    def display(self):
        """Write display buffer to physical display."""
        self.write_command(SSD1306_COLUMNADDR)
        self.write_command(0)              # Column start address. (0 = reset)
        self.write_command(self.width-1)   # Column end address.
        self.write_command(SSD1306_PAGEADDR)
        self.write_command(0)              # Page start address. (0 = reset)
        self.write_command(self._pages-1)  # Page end address.
        # Write buffer data.
        for i in range(0, len(self._buffer), 16):
            control = 0x40   # Co = 0, DC = 0
            self._i2c.write_i2c_block_data(control, self._buffer[i:i+16])

    def image(self, image):
        """Set buffer to value of Python Imaging Library image.  The image should
        be in 1 bit mode and a size equal to the display size.
        """
        if image.mode != '1':
            raise ValueError('Image must be in mode 1.')
        imwidth, imheight = image.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError('Image must be same dimensions as display ({0}x{1}).' \
                .format(self.width, self.height))
        # Grab all the pixels from the image, faster than getpixel.
        pix = image.load()
        # Iterate through the memory pages
        index = 0
        for page in range(self._pages):
            # Iterate through all x axis columns.
            for x in range(self.width):
                # Set the bits for the column of pixels at the current position.
                bits = 0
                # Don't use range here as it's a bit slow
                for bit in [0, 1, 2, 3, 4, 5, 6, 7]:
                    bits = bits << 1
                    bits |= 0 if pix[(x, page*8+7-bit)] == 0 else 1
                # Update buffer byte and increment to next byte.
                self._buffer[index] = bits
                index += 1

    def clear(self):
        """Clear contents of image buffer."""
        self._buffer = [0x00]*(self.width*self._pages)

    def set_contrast(self, contrast):
        """Sets the contrast of the display.  Contrast should be a value between
        0 and 255."""
        if contrast < 0 or contrast > 255:
            raise ValueError('Contrast must be a value from 0 to 255 (inclusive).')
        self.write_command(SSD1306_SETCONTRAST)
        self.write_command(contrast)

    def dim(self, dim):
        """Adjusts contrast to dim the display if dim is True, otherwise sets the
        contrast to normal brightness if dim is False.
        """
        # Assume dim display.
        contrast = 0
        # Adjust contrast based on VCC if not dimming.
        if not dim:
            if self._vccstate == SSD1306_EXTERNALVCC:
                contrast = 0x9F
            else:
                contrast = 0xCF
            self.set_contrast(contrast)

class SSD1306_128_64(SSD1306Base):
    def __init__(self, i2c_bus=None, i2c_address=SSD1306_I2C_ADDRESS_1,
                 i2c=None):
        # Call base class constructor.
        super(SSD1306_128_64, self).__init__(128, 64, i2c_bus, i2c_address, i2c)

    def _initialize(self):
        # 128x64 pixel specific initialization.
        self.write_command(SSD1306_DISPLAYOFF)                    # 0xAE
        self.write_command(SSD1306_SETDISPLAYCLOCKDIV)            # 0xD5
        self.write_command(0x80)                                  # the suggested ratio 0x80
        self.write_command(SSD1306_SETMULTIPLEX)                  # 0xA8
        self.write_command(0x3F)
        self.write_command(SSD1306_SETDISPLAYOFFSET)              # 0xD3
        self.write_command(0x0)                                   # no offset
        self.write_command(SSD1306_SETSTARTLINE | 0x0)            # line #0
        self.write_command(SSD1306_CHARGEPUMP)                    # 0x8D
        if self._vccstate == SSD1306_EXTERNALVCC:
            self.write_command(0x10)
        else:
            self.write_command(0x14)
        self.write_command(SSD1306_MEMORYMODE)                    # 0x20
        self.write_command(0x00)                                  # 0x0 act like ks0108
        self.write_command(SSD1306_SEGREMAP | 0x1)
        self.write_command(SSD1306_COMSCANDEC)
        self.write_command(SSD1306_SETCOMPINS)                    # 0xDA
        self.write_command(0x12)
        self.write_command(SSD1306_SETCONTRAST)                   # 0x81
        if self._vccstate == SSD1306_EXTERNALVCC:
            self.write_command(0x9F)
        else:
            self.write_command(0xCF)
        self.write_command(SSD1306_SETPRECHARGE)                  # 0xd9
        if self._vccstate == SSD1306_EXTERNALVCC:
            self.write_command(0x22)
        else:
            self.write_command(0xF1)
        self.write_command(SSD1306_SETVCOMDETECT)                 # 0xDB
        self.write_command(0x40)
        self.write_command(SSD1306_DISPLAYALLON_RESUME)           # 0xA4
        self.write_command(SSD1306_NORMALDISPLAY)                 # 0xA6

class Rect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.x2 = self.x + self.width
        self.y2 = self.y + self.height

    def coord(self):
        return (self.x, self.y)
    def topcenter(self):
        return (self.x + self.width/2, self.y)
    def size(self):
        return (self.width, self.height)
    def rect(self, pecent=100):
        return (self.x, self.y, self.x + int(self.width*pecent/100.0), self.y2)

class I2cNotEnabled(Exception):
    """I2C总线未启用的异常"""
    def __init__(self, message="I2C interface not enabled"):
        super().__init__(message)
        self.advice = (
            "请检查以下配置：\n"
            "1. 在Raspberry Pi上启用I2C：sudo raspi-config → Interface Options → I2C → Yes\n"
            "2. 确认硬件连接正常\n"
            "3. 加载i2c-dev模块：sudo modprobe i2c-dev"
        )

class OLEDNotDetected(Exception):
    """OLED未检测到的异常"""
    def __init__(self, message="OLED is not detected"):
        super().__init__(message)
        self.advice = (
            "确认OLED已正确连接\n" 
        )
    
class SSD1306():
    def __init__(self):
        self._is_ready = False
        self.oled = None
        self.rotation = 0
        if not I2C.enabled():
            raise I2cNotEnabled()
        addresses = self.check_oled()
        if len(addresses)==0:
            raise OLEDNotDetected()
        self.oled = SSD1306_128_64(i2c_address=addresses[0])
        self.init()
        self._is_ready = True

    def set_rotation(self, rotation):
        self.rotation = rotation

    def is_ready(self):
        return self._is_ready

    def check_oled(self):
        addressed = I2C.scan()
        result = []
        if SSD1306_I2C_ADDRESS_1 in addressed:
            result.append(SSD1306_I2C_ADDRESS_1)
        if SSD1306_I2C_ADDRESS_2 in addressed:
            result.append(SSD1306_I2C_ADDRESS_2)
        return result

    def init(self):
        self.width = self.oled.width
        self.height = self.oled.height
        self.oled.begin()
        self.oled.clear()
        self.oled.on()

        self.image = Image.new('1', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        # self.font_path = str(resource_files(__package_name__).joinpath('fonts/Minecraftia-Regular.ttf'))
        self.font_path = str(resource_files(__package_name__).joinpath('fonts/UbuntuSans-Regular.ttf'))


    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.oled.clear()

    def draw_text(self, text, x, y, fill=1, align='left', size=8, font_path=None):
        text = str(text)
        if font_path is None:
            font = ImageFont.truetype(self.font_path, size)
        else:
            font = ImageFont.truetype(font_path, size)
        text_width = font.getlength(text)
        if align == 'center':
            x -= text_width / 2
        elif align == 'right':
            x -= text_width
        self.draw.text((x, y), text=text, font=font, fill=fill)

    def draw_bar_graph_horizontal(self, percent, x, y, width, height):
        self.draw.rectangle((x, y, x+width, y+height), outline=1, fill=0)
        self.draw.rectangle((x, y, x+int(width*percent/100.0), y+height), outline=1, fill=1)

    def draw_bar_graph_vertical(self, percent, x, y, width, height):
        self.draw.rectangle((x, y, x+width, y+height), outline=1, fill=0)
        self.draw.rectangle((x, y+height-int(height*percent/100.0), x+width, y+height), outline=1, fill=1)

    def draw_pieslice_chart(self, percent, x, y, r, start, end):
        '''
        x, y: pieslice origin
        r: radius
        percent: 0-100
        start, end: pieslice start and end angle
        fill: fill color
        '''
        dir = 1 if start < end else -1
        value_end = int(start + (end-start) * percent / 100) * dir
        self.draw.pieslice((x-r, y-r, x+r, y+r), start=start, end=end, fill=0, outline=1)
        self.draw.pieslice((x-r, y-r, x+r, y+r), start=start, end=value_end, fill=1, outline=1)

    def draw_icon(self, icon, x, y, scale=1.0, invert=False,  dither=True, threshold=127):
        img = Image.open(icon)

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # 缩放
        if scale != 1.0:
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
        self.image.paste(final_img, (x, y), None)


    def display(self):
        image = self.image.rotate(self.rotation)
        self.oled.image(image)
        # save image to file for debug
        # image.save('/tmp/oled.png')
        self.oled.display()

    def off(self):
        self.oled.off()


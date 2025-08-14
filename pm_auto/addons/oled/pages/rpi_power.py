from pm_auto.libs.utils import get_icon, get_font
from pm_auto.libs.oled_page import OLEDPage

font = get_font('UbuntuSans-Regular.ttf')

output_icon = get_icon('raspberry_icon_48.png')
sunfounder_icon = get_icon('sunfounder.ico')

class PageRPiPower(OLEDPage):
    def __init__(self):
        super().__init__()

    def main(self, oled, data, config):
        output_voltage = data.get('output_voltage', 0) / 1000   
        output_current = data.get('output_current', 0) / 1000
        output_power = output_voltage * output_current

        oled.clear()

        oled.draw_icon(output_icon, 76, 12, scale=1, dither=False, threshold=127)
        oled.draw_icon(sunfounder_icon, 105, 40, scale=0.8, dither=False, threshold=130)

        oled.draw_text('RPI Power', 0, 0, size=14, font_path=font)
        oled.draw_text(f'  {output_voltage:.3f} V', 0, 16, size=16, font_path=font)
        oled.draw_text(f'  {output_current:.3f} A', 0, 16*2, size=16, font_path=font)
        oled.draw_text(f'  {output_power:.3f} W', 0, 16*3, size=16, font_path=font)

        oled.display()
        
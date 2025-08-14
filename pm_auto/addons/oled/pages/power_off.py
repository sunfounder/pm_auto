from pm_auto.libs.utils import get_font
from pm_auto.libs.oled_page import OLEDPage

font = get_font('UbuntuSans-Regular.ttf')

class PagePowerOff(OLEDPage):
    def main(self, oled):
        oled.clear()
        oled.draw_text(f'POWER OFF', 64, 20, align='center', size=24, font_path=font)
        oled.display()

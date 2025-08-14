from pm_auto.libs.oled_page import OLEDPage
from pm_auto.libs.utils import get_icon, get_font

charging_icon = get_icon('icon_charge_20.png')
battery_icon = get_icon('icon_battery_40.png')
font = get_font('UbuntuSans-Regular.ttf')

class PageBattery(OLEDPage):
    def __init__(self):
        super().__init__()
        self.charge_bar_val = 0
        self.blink_flag = True

    def main(self, oled, data, config):
        battery_voltage = data.get('battery_voltage', 0) / 1000
        battery_current = data.get('battery_current', 0) / 1000
        battery_power = battery_voltage * battery_current

        battery_percentage = data.get('battery_percentage', 0)
        is_charging = data.get('is_charging', 0)

        oled.clear()

        oled.draw_icon(battery_icon, 64, 10, scale=1, invert=False, dither=False, threshold=127)

        oled.draw_text('BATTERY', 0, 0, size=14, font_path=font)
        oled.draw_text(f'  {battery_voltage:.3f} V', 0, 16, size=16, font_path=font)
        oled.draw_text(f'  {battery_current:.3f} A', 0, 16*2, size=16, font_path=font)
        oled.draw_text(f'  {battery_power:.3f} W', 0, 16*3, size=16, font_path=font)

        if battery_percentage < 100:
            oled.draw_text(f'{battery_percentage:d}', 98, 25, size=24, font_path=font)
        else:
            oled.draw_text(f'{battery_percentage:d}', 96, 30, size=18, font_path=font)

        if is_charging:
            oled.draw_icon(charging_icon, 100, 8, scale=1, invert=False, dither=False, threshold=127)
            _percent = battery_percentage + self.charge_bar_val
            self.charge_bar_val += 15
            if _percent > 100:
                self.charge_bar_val = 0
                _percent = 100

            # oled.draw_bar_graph_vertical(_percent, 76, 16, 15, 30)
            x = 79
            y = 20
            width = 9
            height = 22
            oled.draw.rectangle((x, y+height-int(height*_percent/100.0), x+width, y+height), outline=1, fill=1)

        else:
            # oled.draw_bar_graph_vertical(battery_percentage, 76, 16, 15, 30)
            x = 79
            y = 20
            width = 9
            height = 22
            oled.draw.rectangle((x, y+height-int(height*battery_percentage/100.0), x+width, y+height), outline=1, fill=1)

            power_source = data["power_source"]
            if power_source == 0:
                # oled.draw_text('discharging', 100, 8, size=8)
                if self.blink_flag:
                    self.blink_flag = False
                    oled.draw_icon(charging_icon, 98, 8, scale=1, invert=False, dither=False, threshold=127)
                    oled.draw_text('-', 112, 0, size=36, font_path=font)
                else:
                    self.blink_flag = True

        oled.display()
        
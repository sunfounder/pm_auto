from pm_auto.libs.utils import get_icon, format_bytes, get_font
from pm_auto.libs.oled_page import OLEDPage

font = get_font('UbuntuSans-Regular.ttf')

cpu_icon = get_icon('icon_cpu_24.png')
ram_icon = get_icon('icon_ram_24.png')
temp_icon = get_icon('icon_temperature_24.png')
fan_icon = get_icon('icon_fan_24.png')

class PagePerformance(OLEDPage):
    def __init__(self):
        super().__init__()
        self.cycle_time_start = 0

    def main(self, oled, data, config):
        temperature_unit = config['temperature_unit']
        cpu_temp_c = data.get("cpu_temperature", 0)
        cpu_temp_f = cpu_temp_c * 9 / 5 + 32
        
        cpu_usage = data.get("cpu_percent", 0)
        if cpu_usage >= 100:
            cpu_usage = 100

        temp = cpu_temp_c if temperature_unit == 'C' else cpu_temp_f

        memory_total = data.get("memory_total", 0)
        memory_used = data.get("memory_used", 0)
        memory_percent = data.get("memory_percent", 0)
        memory_total, memory_unit = format_bytes(memory_total)
        memory_used = format_bytes(memory_used, memory_unit)
        if memory_percent >= 100:
            memory_percent = 100

        fan_speed = data.get("pwm_fan_speed", 0)

        oled.clear()

        oled.draw_icon(cpu_icon, 0, 2, scale=1, invert=False)
        oled.draw_text('CPU', 28, 0, size=10, font_path=font)
        oled.draw_text(f"{cpu_usage}%", 25, 10, size=16, font_path=font)

        oled.draw_icon(ram_icon, 0, 32, scale=1, invert=False, dither=False, threshold=127)
        oled.draw_text('RAM', 28, 30, size=10, font_path=font)
        oled.draw_text(f"{memory_percent}%", 25, 38, size=14, font_path=font)
        oled.draw_text(f"{memory_used} / {memory_total} {memory_unit}", 0, 53, size=12, font_path=font)

        oled.draw_icon(temp_icon, 70, 2, scale=1, invert=False)
        oled.draw_text('TEMP', 93, 0, size=10, font_path=font)
        if temperature_unit == 'C':
            oled.draw_text(f"{int(temp):d}°{temperature_unit}", 91, 10, size=16, font_path=font)
        else:
            oled.draw_text(f"{int(temp):d}°{temperature_unit}", 91, 10, size=14, font_path=font)

        oled.draw_icon(fan_icon, 69, 33, scale=1, invert=False, dither=False, threshold=127)
        oled.draw_text('FAN', 95, 32, size=10, font_path=font)
        oled.draw_text(f"{fan_speed}", 93, 42, size=16, font_path=font)

        oled.display()


from pm_auto.libs.utils import get_icon, get_font

cable_plug_icon = get_icon('icon_plug_48.png')
cable_unplug_icon = get_icon('icon_unplug_48.png')

font = get_font('UbuntuSans-Regular.ttf')


def oled_page_input(oled, data, config):
    global charge_bar_val

    input_voltage = data.get('input_voltage' / 1000, 0)
    input_current = data.get('input_current' / 1000, 0)
    input_power = input_voltage * input_current

    is_plugged = data.get('is_input_plugged_in', 0)

    oled.clear()

    if is_plugged:
        oled.draw_icon(cable_plug_icon, 76, 12, scale=1, dither=False, threshold=127)
    else:
        oled.draw_icon(cable_unplug_icon, 76, 12, scale=1, dither=False, threshold=127)

    oled.draw_text('INPUT', 0, 0, size=14, font_path=font)
    oled.draw_text(f'  {input_voltage:.3f} V', 0, 16, size=16, font_path=font)
    oled.draw_text(f'  {input_current:.3f} A', 0, 16*2, size=16, font_path=font)
    oled.draw_text(f'  {input_power:.3f} W', 0, 16*3, size=16, font_path=font)

    oled.display()
    
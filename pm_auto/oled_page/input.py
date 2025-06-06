from pipower5 import PiPower5

from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
cable_plug_icon = str(grandparent_dir) + '/icons/cable_plug_icon_48.png'
cable_unplug_icon = str(grandparent_dir) + '/icons/cable_unplug_icon_48.png'

pipower5 = PiPower5()

def oled_page_input(oled):
    global charge_bar_val
    data_buffer = pipower5.read_all()

    input_voltage = data_buffer['input_voltage'] / 1000   
    # input_current = data_buffer['input_current'] / 1000
    input_current = 0
    input_power = input_voltage * input_current

    is_plugged = data_buffer['is_input_plugged_in']

    oled.clear()

    if is_plugged:
        oled.draw_icon(cable_plug_icon, 76, 12, scale=1, dither=False, threshold=127)
    else:
        oled.draw_icon(cable_unplug_icon, 76, 12, scale=1, dither=False, threshold=127)

    oled.draw_text('INPUT', 0, 0, size=14)
    oled.draw_text(f'  {input_voltage:.3f} V', 0, 16, size=16)
    oled.draw_text(f'  {input_current:.3f} A', 0, 16*2, size=16)
    oled.draw_text(f'  {input_power:.3f} W', 0, 16*3, size=16)


    oled.display()
    
from pipower5 import PiPower5

from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
charging_icon = str(grandparent_dir) + '/icons/charge_icon_20.png'
battery_icon = str(grandparent_dir) + '/icons/battery_icon_40.png'  

pipower5 = PiPower5()

charge_bar_val = 0
blink_flag = True

def oled_page_battery(oled):
    global charge_bar_val, blink_flag
    data_buffer = pipower5.read_all()

    battery_voltage = data_buffer['battery_voltage'] / 1000   
    battery_current = data_buffer['battery_current'] / 1000
    battery_power = battery_voltage * battery_current

    battery_percentage = data_buffer['battery_percentage']
    is_charging = data_buffer['is_charging']

    oled.clear()

    oled.draw_icon(battery_icon, 64, 10, scale=1, invert=False, dither=False, threshold=127)

    oled.draw_text('BATTERY', 0, 0, size=14)
    oled.draw_text(f'  {battery_voltage:.3f} V', 0, 16, size=16)
    oled.draw_text(f'  {battery_current:.3f} A', 0, 16*2, size=16)
    oled.draw_text(f'  {battery_power:.3f} W', 0, 16*3, size=16)

    if battery_percentage < 100:
        oled.draw_text(f'{battery_percentage:d}', 98, 25, size=24)
    else:
        oled.draw_text(f'{battery_percentage:d}', 96, 30, size=18)

    if is_charging:
        oled.draw_icon(charging_icon, 100, 8, scale=1, invert=False, dither=False, threshold=127)
        _percent = battery_percentage + charge_bar_val
        charge_bar_val += 15
        if _percent > 100:
            charge_bar_val = 0
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

        power_source = pipower5.read_power_source()
        if power_source == pipower5.BATTERY:
            # oled.draw_text('discharging', 100, 8, size=8)
            if blink_flag:
                blink_flag = False
                oled.draw_icon(charging_icon, 98, 8, scale=1, invert=False, dither=False, threshold=127)
                oled.draw_text('-', 112, 0, size=36)
            else:
                blink_flag = True

    oled.display()
    
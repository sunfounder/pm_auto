from pipower5 import PiPower5

from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
charging_icon = str(grandparent_dir) + '/icons/charge_icon_20.png'

pipower5 = PiPower5()

charge_bar_val = 0

def oled_page_battery(oled):
    global charge_bar_val
    data_buffer = pipower5.read_all()

    battery_voltage = data_buffer['battery_voltage'] / 1000   
    battery_current = data_buffer['battery_current'] / 1000
    battery_power = battery_voltage * battery_current

    battery_percentage = data_buffer['battery_percentage']
    is_charging = data_buffer['is_charging']

    oled.clear()

    oled.draw_text('BATTERY:', 0, 0, size=16)
    oled.draw_text(f'  {battery_voltage:.3f} V', 0, 16, size=16)
    oled.draw_text(f'  {battery_current:.3f} A', 0, 16*2, size=16)
    oled.draw_text(f'  {battery_power:.3f} W', 0, 16*3, size=16)

    oled.draw_text(f'{battery_percentage:d}', 96, 25, size=24)
    oled.draw_bar_graph_vertical(100, 78, 12, 8, 5)
    if is_charging:
        oled.draw_icon(charging_icon, 100, 8, scale=1, invert=False)
        _percent = battery_percentage + charge_bar_val
        charge_bar_val += 7
        if _percent > 100:
            charge_bar_val = 0
            _percent = 100

        oled.draw_bar_graph_vertical(_percent, 74, 17, 16, 42)
    else:
        oled.draw_bar_graph_vertical(battery_percentage, 74, 17, 16, 42)

    oled.display()
    
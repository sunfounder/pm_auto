from pipower5 import PiPower5

from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
charging_icon = str(grandparent_dir) + '/icons/charge_icon_20.png'

pipower5 = PiPower5()

charge_bar_val = 0

def oled_page_power(oled):
    global charge_bar_val
    data_buffer = pipower5.read_all()

    input_voltage = data_buffer['input_voltage'] / 1000   
    # input_current = data_buffer['input_current'] / 1000
    input_current = 0

    input_power = input_voltage * input_current

    output_voltage = data_buffer['output_voltage'] / 1000   
    output_current = data_buffer['output_current'] / 1000
    output_power = output_voltage * output_current

    battery_voltage = data_buffer['battery_voltage'] / 1000   
    battery_current = data_buffer['battery_current'] / 1000
    battery_power = battery_voltage * battery_current

    battery_percentage = data_buffer['battery_percentage']
    is_charging = data_buffer['is_charging']

    oled.clear()

    oled.draw_text('POWER:', 0, 0, size=16)
    oled.draw_text(f'  {input_power:.3f} W', 0, 16, size=16)
    oled.draw_text(f'  {output_power:.3f} W', 0, 16*2, size=16)
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
    
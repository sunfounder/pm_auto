from pipower5 import PiPower5

pipower5 = PiPower5()

def oled_page_output(oled):
    global charge_bar_val
    data_buffer = pipower5.read_all()

    output_voltage = data_buffer['output_voltage'] / 1000   
    output_current = data_buffer['output_current'] / 1000
    output_power = output_voltage * output_current

    oled.clear()

    oled.draw_text('OUTPUT:', 0, 0, size=16)
    oled.draw_text(f'  {output_voltage:.3f} V', 0, 16, size=16)
    oled.draw_text(f'  {output_current:.3f} A', 0, 16*2, size=16)
    oled.draw_text(f'  {output_power:.3f} W', 0, 16*3, size=16)

    oled.display()
    
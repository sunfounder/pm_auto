from sf_rpi_status import \
    get_cpu_temperature, \
    get_cpu_percent, \
    get_memory_info, \
    PWMFan

from .uilts import format_bytes

from pathlib import Path
grandparent_dir = Path(__file__).resolve().parent.parent
cpu_icon = str(grandparent_dir) + '/icons/cpu_icon_24.png'
ram_icon = str(grandparent_dir) + '/icons/ram_icon_24.png'
temp_icon = str(grandparent_dir) + '/icons/temperature_icon_24.png'
fan_icon = str(grandparent_dir) + '/icons/fan_icon_24.png'

pwm_fan = PWMFan()

def oled_page_performance(oled, config):

    temperature_unit = config['temperature_unit']

    cpu_temp_c = get_cpu_temperature()
    cpu_temp_f = cpu_temp_c * 9 / 5 + 32
    cpu_usage = get_cpu_percent()
    if cpu_usage >= 100:
        cpu_usage = 100

    temp = cpu_temp_c if temperature_unit == 'C' else cpu_temp_f

    memory_info = get_memory_info()
    memory_total, memory_unit = format_bytes( memory_info.total)
    memory_used = format_bytes(memory_info.used, memory_unit)
    memory_percent =  memory_info.percent
    if memory_percent >= 100:
        memory_percent = 100

    # pwm_fan.set_state(4)
    fan_speed = pwm_fan.get_speed()


    oled.clear()

    oled.draw_icon(cpu_icon, 0, 2, scale=1, invert=False)
    oled.draw_text('CPU', 28, 0, size=10)
    oled.draw_text(f"{cpu_usage}%", 25, 10, size=16)

    oled.draw_icon(ram_icon, 0, 32, scale=1, invert=False, dither=False, threshold=127)
    oled.draw_text('RAM', 28, 30, size=10)
    oled.draw_text(f"{memory_percent}%", 25, 38, size=14)
    oled.draw_text(f"{memory_used} / {memory_total} {memory_unit}", 0, 53, size=12)

    oled.draw_icon(temp_icon, 70, 2, scale=1, invert=False)
    oled.draw_text('TEMP', 93, 0, size=10)
    if temperature_unit == 'C':
        oled.draw_text(f"{int(temp):d}°{temperature_unit}", 91, 10, size=16)
    else:
        oled.draw_text(f"{int(temp):d}°{temperature_unit}", 91, 10, size=14)

    oled.draw_icon(fan_icon, 69, 33, scale=1, invert=False, dither=False, threshold=127)
    oled.draw_text('FAN', 95, 32, size=10)
    oled.draw_text(f"{fan_speed}", 93, 42, size=16)

    oled.display()

import time

def oled_page_power_off(oled):
    oled.clear()
    oled.draw_text(f'POWER OFF', 64, 20, align='center', size=24)
    oled.display()
    time.sleep(1)
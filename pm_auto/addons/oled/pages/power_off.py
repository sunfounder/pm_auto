import asyncio
from pm_auto.libs.utils import get_font

font = get_font('UbuntuSans-Regular.ttf')

async def oled_page_power_off(oled):
    oled.clear()
    oled.draw_text(f'POWER OFF', 64, 20, align='center', size=24, font_path=font)
    oled.display()
    await asyncio.sleep(1)

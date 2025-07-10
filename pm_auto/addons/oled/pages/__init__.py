
def get_pages(page_names):
    pages = []
    for name in page_names:
        if 'battery' == name:
            from .battery import oled_page_battery
            pages.append(oled_page_battery)
        elif 'disk' == name:
            from .disks import oled_page_disk
            pages.append(oled_page_disk)
        elif 'input' == name:
            from .input import oled_page_input
            pages.append(oled_page_input)
        elif 'ips' == name:
            from .ips import oled_page_ips
            pages.append(oled_page_ips)
        elif 'mix' == name:
            from .mix import oled_page_mix
            pages.append(oled_page_mix)
        elif 'output' == name:
            from .output import oled_page_output
            pages.append(oled_page_output)
        elif 'performance' == name:
            from .performance import oled_page_performance
            pages.append(oled_page_performance)
        else:
            raise ValueError(f"Unknown page name: {name}")

    return pages

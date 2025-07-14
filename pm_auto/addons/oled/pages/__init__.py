
from .power_off import Page_Power_Off

power_off_page = Page_Power_Off()

def get_pages(page_names):
    pages = []
    for name in page_names:
        if 'battery' == name:
            from .battery import Page_Battery
            pages.append(Page_Battery())
        elif 'disk' == name:
            from .disks import Page_Disk
            pages.append(Page_Disk())
        elif 'input' == name:
            from .input import Page_Input
            pages.append(Page_Input())
        elif 'ips' == name:
            from .ips import Page_IPs
            pages.append(Page_IPs())
        elif 'mix' == name:
            from .mix import Page_Mix
            pages.append(Page_Mix())
        elif 'rpi_power' == name:
            from .rpi_power import Page_RPi_Power
            pages.append(Page_RPi_Power())
        elif 'performance' == name:
            from .performance import Page_Performance
            pages.append(Page_Performance())
        else:
            raise ValueError(f"Unknown page name: {name}")

    return pages

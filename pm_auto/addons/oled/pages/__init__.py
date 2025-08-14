
from .power_off import PagePowerOff

power_off_page = PagePowerOff()

def get_pages(page_names):
    pages = []
    for name in page_names:
        if 'battery' == name:
            from .battery import PageBattery
            pages.append(PageBattery())
        elif 'disk' == name:
            from .disks import PageDisks
            pages.append(PageDisks())
        elif 'input' == name:
            from .input import PageInput
            pages.append(PageInput())
        elif 'ips' == name:
            from .ips import PageIPs
            pages.append(PageIPs())
        elif 'mix' == name:
            from .mix import PageMix
            pages.append(PageMix())
        elif 'rpi_power' == name:
            from .rpi_power import PageRPiPower
            pages.append(PageRPiPower())
        elif 'performance' == name:
            from .performance import PagePerformance
            pages.append(PagePerformance())
        else:
            raise ValueError(f"Unknown page name: {name}")

    return pages

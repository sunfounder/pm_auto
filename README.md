# PM Auto

Pironman Auto is a tool to control all peripherals on your Pironman.

- [PM Auto](#pm-auto)
  - [Installation](#installation)
  - [Usage](#usage)
  - [About SunFounder](#about-sunfounder)
  - [Contact us](#contact-us)

## Installation

```bash
# Install development dependencies
apt-get -y install python3 python3-pip python3-venv git
# for pillow
apt-get -y install libfreetype6-dev libjpeg-dev libopenjp2-7
# Create a virtual environment
python3 -m venv venv
# Install build
pip3 install build

# Clone the repository
git clone https://github.com/sunfounder/pm_auto.git
# Activate the virtual environment
source venv/bin/activate
# build the package
python3 -m build
# Install the package
pip3 install dist/*.whl
```

it depends on influxdb, you can install it with the following command:

```bash
apt install influxdb
systemctl unmask influxdb
systemctl enable influxdb
systemctl start influxdb
```

## Usage

```python
from pm_auto.pm_auto import PMAuto

config = {
    "peripherals": [
      'oled',
      'ws2812',
    ],
    "temperature_unit": "C",
},

pm = PMAuto(config)
pm.start()

```

## About SunFounder
SunFounder is a company focused on STEAM education with products like open source robots, development boards, STEAM kit, modules, tools and other smart devices distributed globally. In SunFounder, we strive to help elementary and middle school students as well as hobbyists, through STEAM education, strengthen their hands-on practices and problem-solving abilities. In this way, we hope to disseminate knowledge and provide skill training in a full-of-joy way, thus fostering your interest in programming and making, and exposing you to a fascinating world of science and engineering. To embrace the future of artificial intelligence, it is urgent and meaningful to learn abundant STEAM knowledge.

## Contact us
website:
    www.sunfounder.com

E-mail:
    service@sunfounder.com

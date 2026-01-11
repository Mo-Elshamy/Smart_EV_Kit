# Smart EV Kit — Project Overview

The Smart EV Kit combines a Raspberry Pi–based Vehicle Control Unit (VCU) and a set of mechanical parts for an educational electric buggy platform. It integrates secure access (NFC), a touchscreen dashboard, ultrasonic safety sensors, and addressable LED lighting for prototyping and learning.

![Front Bar](/images/Final3.jpg)

---

## [Software & Electrical Hardware](software/Software.md)

Overview: The software stack is written in Python and provides a touch-friendly dashboard, hardware abstraction, and background services for sensors and actuators. Key components include the GUI (`main.py` using PyQt5), the hardware abstraction layer (`hardware.py`) which manages GPIO, SPI (NFC), ultrasonic sensors, LED animations, relays, and the DHT sensor loops.

Electrical hardware summary: Designed for a Raspberry Pi 4 with a 7" HDMI touchscreen, the system uses eight HC-SR04 ultrasonics (echo lines protected by voltage dividers), an RC522 NFC reader on SPI, a WS2811 12V LED strip driven via PWM-capable GPIO, a 2-channel relay module (active-low), and a DHT11 environmental sensor. Power conversion is expected via 48V→12V and 48V→5V buck converters.
![Front Bar](/images/image.png)

---

## [Mechanical](mechanical/Mechacinal.md)

Overview: Mechanical assets include 3D-printed mounts, a multi-part control box, sensor bars, and laser-cut acrylic body panels. The documentation lists fitment issues and recommended V2 improvements (tolerance adjustments, mounting standoffs, and cutout updates) and contains a student steering prototype activity.
![Front Bar](/images/final.jpg) | ![Front Bar](/images/final2.jpg)


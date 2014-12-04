
"""
Installation methods to support the installer.

* **board**: for operations that require the board to be attached through a 
  communication port.
* **sd**: for operations to create bootable SD cards.
* **usb**: for operations to create an installer from a bootable USB drive.
"""

import sdcard
import board
import usb

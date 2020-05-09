# ISS_tracker
For astronomer wanting to track the ISS (or any other earth satellite) in the sky with their ASCOM compatible telescope mount. This python program will pilot the telescope mount. It was originally written in Python 2 then futurized to Python 3 and should work with both versions.


# Dependencies
- Install ascom platform 6.3
- Install Ascom driver for mount
- Install Ascom dev components (devlopper components)

Install the following python modules:
- ephem

The other modules should be standard:
- import win32com.client      #needed to load COM objects
- import ephem
- import datetime
- import time
- import winsound
- import sys
- import urllib2
- import re
- import numpy as np

# Usage
The Ephem part download the satellite 2 line elements and compute the track for the location.
The second part use the precomputed track (editable) and commands the mount via ascom to follow the satellite.

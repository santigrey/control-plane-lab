#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/jes/control-plane')
from mqtt_publisher import nudge
nudge("End of day summary: give James a brief end-of-day summary of today's job search, applications, and build progress.")
print('Evening nudge sent')

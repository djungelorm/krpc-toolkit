import krpc
import time
import sys
from krpctoolkit.attitude import *
from krpctoolkit.throttle import *
from krpctoolkit.launch import Launch

conn = krpc.connect(name='Plane Stabiliser')
vessel = conn.space_center.active_vessel

roll = RollController(conn, vessel, 0, vessel.surface_reference_frame)
pitch = PitchController(conn, vessel, 0, vessel.surface_reference_frame)
throttle = ThrottleSpeedController(conn, vessel, 200)

while True:
    roll()
    pitch()
    throttle()
    time.sleep(1)

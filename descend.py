import krpc
import time
import math

def descend_to_surface():
    """ Descend onto the surface of Kerbin using parachutes """

    target_periapsis = 35000

    conn = krpc.connect(name='descend')
    vessel = conn.space_center.active_vessel

    altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
    periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')

    print 'Orienting ship for braking burn'
    vessel.auto_pilot.set_direction((0,-1,0), reference_frame=vessel.orbital_reference_frame, wait=True)

    print 'Executing braking burn'
    vessel.control.throttle = 1
    while periapsis() > target_periapsis:
        pass
    vessel.control.throttle = 0
    time.sleep(1)

    print 'Decoupling descent stage'
    vessel.control.activate_next_stage()

    print 'Descending through atmosphere'
    vessel.auto_pilot.set_direction(
        (0,-1,0), reference_frame=vessel.surface_velocity_reference_frame, wait=True)
    while altitude() > 1000:
        time.sleep(1)
    vessel.auto_pilot.disengage()

    print 'Deploying chutes'
    for parachute in vessel.parts.parachutes:
        parachute.deploy()

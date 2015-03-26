import krpc
import time
import math

def launch_to_altitude(target_altitude):
    """
    Launch a rocket into a circular orbit at a chosen altitude.
    Staging must be done manually.
    """

    turn_start_altitude = 250
    turn_end_altitude = 45000
    atmosphere_altitude = 70500

    conn = krpc.connect(name='launch_to_altitude')
    vessel = conn.space_center.active_vessel

    # Set up streams for telemetry
    ut = conn.add_stream(getattr, conn.space_center, 'ut')
    altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
    apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
    periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
    eccentricity = conn.add_stream(getattr, vessel.orbit, 'eccentricity')

    # Pre-launch setup
    vessel.control.sas = False
    vessel.control.rcs = False
    vessel.control.throttle = 1
    vessel.auto_pilot.set_rotation(90, 90)

    # Launch
    time.sleep(1)
    print 'Waiting for launch'
    stage = vessel.control.current_stage
    while stage == vessel.control.current_stage:
        time.sleep(1)

    # Main ascent loop
    turn_angle = 0
    while True:

        # Gravity turn
        if altitude() > turn_start_altitude and altitude() < turn_end_altitude:
            frac = (altitude() - turn_start_altitude) / (turn_end_altitude - turn_start_altitude)
            new_turn_angle = frac * 90
            if abs(new_turn_angle - turn_angle) > 0.5:
                turn_angle = new_turn_angle
                vessel.auto_pilot.set_rotation(90-turn_angle, 90)

        # Decrease throttle when approaching target apoapsis
        # TODO: more robust to estimate remaining burn time, and stop when there is < 10s
        if apoapsis() > target_altitude * 0.9:
            print 'Approaching target apoapsis'
            break

    # Disable engines when target apoapsis is reached
    vessel.control.throttle = 0.25 # TODO: work out what this should be from thrust
    while apoapsis() < target_altitude:
        pass
    print 'Target apoapsis reached'
    vessel.control.throttle = 0

    # Wait until out of atmosphere
    print 'Coasting out of atmosphere'
    while altitude() < atmosphere_altitude:
        pass

    # Plan circularization burn (using vis-viva equation)
    print 'Planning circularization burn'
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    vessel.control.remove_nodes()
    node = vessel.control.add_node(ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)

    # Calculate burn time (using rocket equation)
    F = vessel.thrust
    Isp = vessel.specific_impulse * 9.82
    m0 = vessel.mass
    m1 = m0 / math.exp(delta_v/Isp)
    flow_rate = F / Isp
    burn_time = (m0 - m1) / flow_rate

    # Orientate ship
    print 'Orientating ship for circularization burn'
    vessel.auto_pilot.set_direction((0,1,0), reference_frame=node.reference_frame, wait=True)

    # Wait until burn
    print 'Waiting until circularization burn'
    burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time/2.)
    lead_time = 5
    conn.space_center.warp_to(burn_ut - lead_time)

    # Execute burn
    print 'Ready to execute burn'
    remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
    while ut() < burn_ut:
        pass
    print 'Executing burn'
    vessel.control.throttle = 1

    # Fine tune at 10m/s to go
    # TODO: more robust to compute this from thrust of engines
    while remaining_burn()[1] > 50:
        print remaining_burn()
        pass

    print 'Fine tuning'
    vessel.control.throttle = 0.05 # TODO: compute this from thrust of engines
    while remaining_burn()[1] > 0:
        print remaining_burn()
        pass
    print remaining_burn()
    vessel.control.throttle = 0
    node.remove()

    print 'Launch complete'

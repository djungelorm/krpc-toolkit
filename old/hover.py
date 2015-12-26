import krpc

conn = krpc.connect()
vessel = conn.space_center.active_vessel

print('Waiting for launch')
while vessel.situation != conn.space_center.VesselSituation.flying:
    pass
print('Running')

control = vessel.control
flight = vessel.flight(vessel.orbit.body.reference_frame)

altitude = conn.add_stream(getattr, flight, 'surface_altitude')
mass = conn.add_stream(getattr, vessel, 'mass')
g_force = conn.add_stream(getattr, flight, 'g_force')
vertical_speed = conn.add_stream(getattr, flight, 'vertical_speed')
max_thrust = sum(e.max_thrust for e in vessel.parts.engines)

while vessel.situation == conn.space_center.VesselSituation.flying:
    alt_error = 20.0 - altitude()
    throttle = (mass() * (g_force() - vertical_speed() + alt_error)) / max_thrust
    throttle = max(min(1, throttle), 0)
    control.throttle = throttle
    print('.2f%\r', altitude())
    import time
    time.sleep(0.1)

print('Done')

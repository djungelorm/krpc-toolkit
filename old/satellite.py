import ascend
import descend
import krpc
import threading
import time

conn = krpc.connect()
vessel = conn.space_center.active_vessel

#def jettison_fairings():
#    fairings = vessel.parts.modules_with_name('ProceduralFairingDecoupler')
#    for fairing in fairings:
#        fairing.trigger_event('Jettison')
#
#def jettison_fairings_thread():
#    vessel = conn.space_center.active_vessel
#    flight = vessel.flight()
#    while flight.mean_altitude < 70000:
#        time.sleep(5)
#    jettison_fairings()
#
#t = threading.Thread(target=jettison_fairings_thread)
#t.daemon = True
#t.start()
#ascend.launch_to_altitude(100000, turn_end_altitude=100000)
#t.join()
#
#print 'Deploying satellite'
#
#for panel in vessel.parts.solar_panels:
#    panel.deployed = True
#
#for aerial in vessel.parts.with_module('ModuleRTAntenna'):
#    for m in aerial.modules:
#        if m.name == 'ModuleRTAntenna':
#            if m.has_event('Activate'):
#                m.trigger_event('Activate')
#
#time.sleep(10)
#
#vessel.control.activate_next_stage()
#
#print 'Returning launcher to kerbin'
#
target_periapsis = 35000

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

print 'Uncovering heat shield'
vessel.control.activate_next_stage()

print 'Orienting ship for descent'
vessel.auto_pilot.set_direction((0,1,0), reference_frame=vessel.surface_velocity_reference_frame, wait=True)

while altitude() > 10000:
    time.sleep(1)
vessel.auto_pilot.disengage()

print 'Descending through atmosphere'
while altitude() > 1000:
    time.sleep(1)
vessel.auto_pilot.disengage()

print 'Deploying chutes'
for parachute in vessel.parts.parachutes:
    parachute.deploy()

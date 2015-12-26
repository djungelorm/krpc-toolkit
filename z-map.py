import krpc
import time
from krpctoolkit.launch import Ascend
from krpctoolkit.staging import AutoStage
from krpctoolkit.maneuver import circularize, ExecuteNode

target_altitude = 100000

conn = krpc.connect(name='Z-MAP')
vessel = conn.space_center.active_vessel

print('Launching')
ascend = Ascend(conn, vessel, target_altitude)
staging = AutoStage(conn, vessel)
while not ascend():
    staging()
    time.sleep(0.1)

vessel.auto_pilot.max_rotation_speed = 0.2
vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
vessel.auto_pilot.target_direction = (0,1,0)
vessel.auto_pilot.target_roll = float('nan')
vessel.auto_pilot.engage()

print('Coasting out of atmosphere')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
atmosphere_altitude = vessel.orbit.body.atmosphere_depth * 1.01
while altitude() < atmosphere_altitude:
    pass

print('Circularizing')
vessel.control.remove_nodes()
node = circularize(conn, vessel)
execute = ExecuteNode(conn, vessel, node)
while not execute():
    staging()
    time.sleep(0.1)
node.remove()

vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
vessel.auto_pilot.target_direction = (0,1,0)
vessel.auto_pilot.target_roll = float('nan')
vessel.auto_pilot.engage()

print('Deploying Satellite')
for part in vessel.parts.all:
    for module in part.modules:
        if module.name == 'ModuleAnimateGeneric':
            if module.has_event('Extend'):
                module.trigger_event('Extend')
vessel.control.activate_next_stage()

print('Complete')

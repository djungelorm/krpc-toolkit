import krpc

conn = krpc.connect(name='Z-MAP')
vessel = conn.space_center.active_vessel

vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
vessel.auto_pilot.target_direction = (0,1,0)
vessel.auto_pilot.target_roll = float('nan')
vessel.auto_pilot.engage()
vessel.auto_pilot.wait()

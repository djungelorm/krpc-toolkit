import krpc
import time
import math
from krpctoolkit.throttle import *
from krpctoolkit.attitude import *

class Ascend(object):
    """
    Launch a rocket to a target apoapsis with zero inclination.
    """

    def __init__(self, conn, vessel, target_altitude):
        self.conn = conn
        self.vessel = vessel
        self.turn_start_altitude = 250
        self.turn_end_altitude = self.vessel.orbit.body.atmosphere_depth * 0.75
        self.target_altitude = target_altitude
        self.max_q = 7000

        # Set up streams for telemetry
        self.ut = self.conn.add_stream(getattr, self.conn.space_center, 'ut')
        self.altitude = self.conn.add_stream(getattr, self.vessel.flight(), 'mean_altitude')
        self.apoapsis = self.conn.add_stream(getattr, self.vessel.orbit, 'apoapsis_altitude')
        self.periapsis = self.conn.add_stream(getattr, self.vessel.orbit, 'periapsis_altitude')
        self.eccentricity = self.conn.add_stream(getattr, self.vessel.orbit, 'eccentricity')

        # Set up controllers
        self.throttle_controller = ThrottleMaxQController(self.conn, self.vessel, max_q=self.max_q)
        self.auto_pilot = vessel.auto_pilot

        # Pre-launch setup
        self.vessel.control.sas = False
        self.vessel.control.rcs = False
        self.vessel.control.throttle = 1
        self.auto_pilot.reference_frame = vessel.surface_reference_frame
        self.auto_pilot.target_pitch_and_heading(90,90)
        self.auto_pilot.target_roll = float('nan')
        self.auto_pilot.engage()

    def __call__(self):
        if self.altitude() < self.turn_start_altitude:
            self.auto_pilot.target_pitch_and_heading(90,90)
        elif self.turn_start_altitude < self.altitude() and self.altitude() < self.turn_end_altitude:
            frac = (self.altitude()-self.turn_start_altitude) / (self.turn_end_altitude-self.turn_start_altitude)
            self.auto_pilot.target_pitch_and_heading(90*(1-frac),90)
        else:
            self.auto_pilot.target_pitch_and_heading(0,90)

        if self.apoapsis() > self.target_altitude:
            self.vessel.control.throttle = 0
            self.auto_pilot.disengage()
            return True
        else:
            self.throttle_controller()
            return False

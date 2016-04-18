#https://ghowen.me/build-your-own-quadcopter-autopilot/
import numpy as np
from krpctoolkit.pid import PIDController
import math

class RollController(object):
    def __init__(self, conn, vessel, target, ref, mult=1):
        self.control = vessel.control
        self.target = target * (math.pi/180.)
        self.roll = conn.add_stream(getattr, vessel.flight(ref), 'roll')
        self.mult = mult

    def __call__(self):
        roll = self.error * self.mult
        self.control.roll = roll

    @property
    def error(self):
        return self.target - self.roll()

class PitchController(object):
    def __init__(self, conn, vessel, target, ref, mult=1):
        self.control = vessel.control
        self.target = target * (math.pi/180.)
        #self.velocity = conn.add_stream(getattr, vessel.flight(ref), 'prograde')
        self.velocity = lambda: vessel.flight(ref).prograde
        self.mult = mult

    def __call__(self):
        pitch = self.error * self.mult
        self.control.pitch = float(pitch) #TODO: why is this double?!?!

    @property
    def error(self):
        angle = np.dot(self.velocity(), (1,0,0))
        return (self.target/2) - angle

class RotationRateController(object):
    def __init__(self, conn, vessel, target, ref):
        self.pid = PIDController()
        self.target = np.array(target)
        self._control = vessel.control
        self._velocity = conn.add_stream(vessel.angular_velocity, ref)
        self._pitch_dir = conn.add_stream(
            conn.space_center.transform_direction, (1,0,0), vessel.reference_frame, ref)
        self._yaw_dir = conn.add_stream(
            conn.space_center.transform_direction, (0,0,1), vessel.reference_frame, ref)
        self._roll_dir = conn.add_stream(vessel.direction, ref)

    def __call__(self):
        output = self.pid.update(self.error, self.target, (-1,-1,-1), (1,1,1))
        self._control.pitch = float(output[0])
        self._control.yaw = float(output[1])
        self._control.roll = float(output[2])

    @property
    def error(self):
        err = self.target - np.array(self._velocity())
        pitch = np.dot(err, self._pitch_dir())
        yaw = np.dot(err, self._yaw_dir())
        roll = np.dot(err, self._roll_dir())
        return np.array((pitch, yaw, roll))

class AttitudeController(object):
    def __init__(self, conn, vessel, target_direction, target_roll, ref):
        self.target_direction = target_direction
        self.target_roll = target_roll
        self._direction = conn.add_stream(vessel.direction, ref)
        self._roll = conn.add_stream(getattr, vessel.flight(ref), 'roll')
        self.rate_controller = RotationRateController(conn, vessel, (0,0,0), ref)
        self.pid = self.rate_controller.pid

    def __call__(self):
        self.rate_controller.target = np.cross(self.target_direction, np.array(self._direction()))
        if self.target_roll is not None:
            self.rate_controller.target += self.target_direction * (self.roll_error/90)
        self.rate_controller()

    @property
    def target_direction(self):
        return self._target_direction

    @target_direction.setter
    def target_direction(self, direction):
        self._target_direction = np.array(direction) / np.linalg.norm(direction)

    @property
    def target_roll(self):
        return self._target_roll

    @target_roll.setter
    def target_roll(self, roll):
        self._target_roll = roll

    @property
    def error(self):
        return self.target_direction - np.array(self._direction())

    @property
    def roll_error(self):
        if self.target_roll is None:
            return 0
        return self.target_roll - self._roll()

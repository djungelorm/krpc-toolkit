from krpctoolkit.controller import Controller

class ThrottleMaxQController(Controller):
    def __init__(self, conn, vessel, max_q):
        self.control = vessel.control
        flight = vessel.flight(vessel.orbit.body.reference_frame)
        self.q = conn.add_stream(getattr, flight, 'dynamic_pressure')
        self.max_q = max_q

    def pv(self):
        return self.q()

    def setpoint(self):
        return self.max_q

    def mv(self, x):
        self.control.throttle = x

class ThrottleSpeedController(Controller):
    def __init__(self, conn, vessel, max_speed):
        self.control = vessel.control
        flight = vessel.flight(vessel.orbit.body.reference_frame)
        self.speed = conn.add_stream(getattr, flight, 'speed')
        self.max_speed = max_speed

    def pv(self):
        return self.speed()

    def setpoint(self):
        return self.max_speed

    def mv(self, x):
        self.control.throttle = x

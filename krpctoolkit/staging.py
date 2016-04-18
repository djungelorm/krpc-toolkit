import time

class AutoStage(object):
    def __init__(self, conn, vessel, delay=1):
        self.vessel = vessel
        self.delay = delay
        self.wait_until = 0

    def __call__(self):
        if time.time() < self.wait_until:
            return
        stage = self.vessel.control.current_stage
        parts = self.vessel.parts.in_decouple_stage(stage-1)
        for part in parts:
            engine = part.engine
            if engine and engine.active and engine.has_fuel:
                return
        self.vessel.control.activate_next_stage()
        self.wait_until = time.time() + self.delay

import numpy as np

class PIDController(object):
    """ Robust, single parameter, proportional-integral-derivative controller
        http://brettbeauregard.com/blog/2011/04/improving-the-beginners-pid-introduction/ """

    def __init__(self, Kp = 1, Ki = 0, Kd = 0, dt = 1):
        self.setparams(Kp, Ki, Kd, dt)
        self.Ti = 0
        self.last_position = 0

    def setparams(self, Kp = 1, Ki = 0, Kd = 0, dt = 1):
        self.Kp = Kp
        self.Ki = Ki * dt
        self.Kd = Kd / dt

    def update(self, error, position, min_output, max_output):
        self.Ti += self.Ki * error
        self.Ti = np.maximum(min_output, np.minimum(max_output, self.Ti))
        dInput = position - self.last_position
        output = self.Kp * error + self.Ti - self.Kd * dInput
        output = np.maximum(min_output, np.minimum(max_output, output))
        self.last_position = position
        return output

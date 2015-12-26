class Controller(object):
    def __call__(self):
        x = self.pv()
        high = self.setpoint() * 1.1
        low = self.setpoint() * 0.9
        if x < low:
            self.mv(1)
        elif x > high:
            self.mv(0)
        else:
            self.mv((high-x) / (high-low))

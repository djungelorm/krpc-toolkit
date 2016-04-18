import krpc
import time
import math
from krpctoolkit.throttle import *
from krpctoolkit.attitude import *
from krpctoolkit.staging import *

def circularize(conn, vessel, at_apoapsis=True):
    orbit = vessel.orbit
    mu = orbit.body.gravitational_parameter
    if at_apoapsis:
        r = orbit.apoapsis
    else:
        r = orbit.periapsis
    a1 = orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    ut = conn.space_center.ut
    if at_apoapsis:
        ut += orbit.time_to_apoapsis
    else:
        ut += orbit.time_to_periapsis
    node = vessel.control.add_node(ut, prograde=delta_v)
    return node

def change_apoapsis(conn, vessel, new_apoapsis):
    orbit = vessel.orbit
    mu = orbit.body.gravitational_parameter
    ut = conn.space_center.ut + orbit.time_to_periapsis
    r1 = orbit.periapsis
    a1 = orbit.semi_major_axis
    v1 = math.sqrt(mu*((2./r1)-(1./a1)))
    r2 = r1
    a2 = (r1 + new_apoapsis) / 2
    v2 = math.sqrt(mu*((2./r2)-(1./a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(ut, prograde=delta_v)
    return node

def change_periapsis(conn, vessel, new_periapsis):
    orbit = vessel.orbit
    mu = orbit.body.gravitational_parameter
    ut = conn.space_center.ut + orbit.time_to_apoapsis
    r1 = orbit.apoapsis
    a1 = orbit.semi_major_axis
    v1 = math.sqrt(mu*((2./r1)-(1./a1)))
    r2 = r1
    a2 = (r1 + new_periapsis) / 2
    v2 = math.sqrt(mu*((2./r2)-(1./a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(ut, prograde=delta_v)
    return node

def change_sma(conn, vessel, sma, ut):
    orbit = vessel.orbit
    mu = orbit.body.gravitational_parameter
    r1 = orbit.radius
    a1 = orbit.semi_major_axis
    v1 = math.sqrt(mu*((2./r1)-(1./a1)))
    r2 = r1
    a2 = sma
    v2 = math.sqrt(mu*((2./r2)-(1./a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(ut, prograde=delta_v)
    return node

def hohmann_transfer(conn, vessel, target):
    orbit = vessel.orbit
    mu = orbit.body.gravitational_parameter
    r1 = orbit.radius
    r2 = target.orbit.radius

    transfer_time = math.pi * math.sqrt(((r1+r2)**3)/(8*mu))
    transfer_angle = math.pi * (1 - (1/(2*math.sqrt(2))) * math.sqrt(((r1/r2)+1)**3))

    Mv = orbit.mean_anomaly
    Mt = target.orbit.mean_anomaly
    av = orbit.semi_major_axis
    at = target.orbit.semi_major_axis
    nv = math.sqrt(mu/(av**3))
    nt = math.sqrt(mu/(at**3))

    Mt += 2*math.pi

    time_until_transfer = (transfer_angle - Mt + Mv) / (nt - nv)

    print(Mt, Mv, transfer_angle, transfer_angle - Mt + Mv, nt - nv, time_until_transfer)

    ut = conn.space_center.ut + time_until_transfer

    a1 = orbit.semi_major_axis
    v1 = math.sqrt(mu*((2./r1)-(1./a1)))
    a2 = (target.orbit.radius + r1) / 2
    v2 = math.sqrt(mu*((2./r1)-(1./a2)))
    delta_v = v2 - v1

    node = vessel.control.add_node(ut, prograde=delta_v)
    return node

def total_area(orbit):
    a = orbit.semi_major_axis
    b = orbit.semi_minor_axis
    return math.pi * a * b

def area_since_periapsis(orbit, E):
    a = orbit.semi_major_axis
    b = orbit.semi_minor_axis
    return 0.5 * a * b * E

def mean_anomaly_from_true_anomaly(orbit, theta):
    e = orbit.eccentricity
    adj = e + math.cos(theta)
    hyp = 1 + e*math.cos(theta)
    return math.acos(adj / hyp)

def area_between_mean_anomalies(orbit, E0, E1):
    A0 = area_since_periapsis(orbit, E0)
    A1 = area_since_periapsis(orbit, E1)
    return A1 - A0

def time_to_ascending_node(orbit):
    A0 = total_area(orbit)

    E = orbit.mean_anomaly
    Ap = area_since_periapsis(orbit, E)

    theta = orbit.argument_of_periapsis - math.pi
    En = mean_anomaly_from_true_anomaly(orbit, theta)
    En += math.pi
    An = area_since_periapsis(orbit, En)

    frac = (An-Ap)/A0
    return orbit.period * frac

def time_to_descending_node(orbit):
    A0 = total_area(orbit)

    E = orbit.mean_anomaly
    Ap = area_since_periapsis(orbit, E)

    theta = orbit.argument_of_periapsis - math.pi
    En = mean_anomaly_from_true_anomaly(orbit, theta)
    An = area_since_periapsis(orbit, En)

    frac = (An-Ap)/A0
    return orbit.period * frac

def change_inclination(conn, vessel, new_inclination):
    orbit = vessel.orbit
    i = new_inclination - orbit.inclination
    v = orbit.speed
    normal = v*math.sin(i)
    prograde = v*math.cos(i) - v
    ut = conn.space_center.ut + time_to_ascending_node(orbit)
    node = vessel.control.add_node(ut, normal=normal, prograde=prograde)
    return node

def execute_node(conn, vessel, node):
    x = ExecuteNode(conn, vessel, node)
    while x():
        time.sleep(0.025)
    node.remove()

class ExecuteNode(object):

    def __init__(self, conn, vessel, node, lead_time=5):
        self.conn = conn
        self.vessel = vessel
        self.node = node
        self.ut = conn.add_stream(getattr, conn.space_center, 'ut')
        self.lead_time = lead_time
        self.remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
        self.node_ut = node.ut

        # Calculate burn time using rocket equation
        F = vessel.available_thrust
        Isp = vessel.specific_impulse * 9.82
        m0 = vessel.mass
        m1 = m0 / math.exp(node.delta_v/Isp)
        flow_rate = F / Isp
        self.burn_time = (m0 - m1) / flow_rate

        # Orientate ship
        ap = vessel.auto_pilot
        ap.reference_frame = node.reference_frame
        ap.target_direction = (0,1,0)
        ap.engage()

    def __call__(self):
        if not self.node:
            return True

        burn_ut = self.node_ut - (self.burn_time/2.)

        #TODO: check vessel is pointing in the correct direction before warping
        #      and if the error is large, drop out of warp and reorient the vessel
        if self.ut() < burn_ut - self.lead_time:
            self.conn.space_center.warp_to(burn_ut - self.lead_time)

        if self.ut() < burn_ut:
            return False

        # Burn time remaining
        try:
            F = self.vessel.available_thrust
            Isp = self.vessel.specific_impulse * 9.82
            m0 = self.vessel.mass
            m1 = m0 / math.exp(self.remaining_burn()[1]/Isp)
            flow_rate = F / Isp
            remaining_burn_time = (m0 - m1) / flow_rate
        except ZeroDivisionError:
            return False

        if remaining_burn_time > 2:
            # Burn at full throttle
            self.vessel.control.throttle = 1
            return False
        elif self.remaining_burn()[1] > 0:
            # Burn at a throttle setting that maintains a
            # remaining burn time of t seconds
            t = 2
            F = ((m0 - m1) / t) * Isp
            throttle = F / self.vessel.available_thrust
            self.vessel.control.throttle = max(0.005, throttle)
            return False
        else:
            # Burn complete
            self.vessel.control.throttle = 0
            self.node = None
            return True

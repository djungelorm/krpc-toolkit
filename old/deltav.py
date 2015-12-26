import krpc
import math
from collections import defaultdict

# Compute the Delta-V in each stage of a rocket

conn = krpc.connect()
parts = conn.space_center.active_vessel.parts

# Get information about parts
parts_info = {}
for part in parts.all:
    parts_info[part] = {
        'parent': part.parent,
        'children': part.children,
        'crossfeed': part.crossfeed,
        'fuel_lines_from': part.fuel_lines_from,
        'axially_attached': part.axially_attached,
        'mass': part.mass,
        'dry_mass': part.dry_mass,
        'stage': part.stage,
        'decouple_stage': part.decouple_stage,
        'resources': [str(x) for x in part.resources.names], # TODO: fix unicode bug
        'engine': part.engine
    }

# Get fuel densities in kg/l
#TODO: get these from KSP
density = {
  'LiquidFuel': 5,
  'Oxidizer': 5,
  'SolidFuel': 7.5,
  'ElectricCharge': 0,
  'MonoPropellant': 4
}

# Get parts decoupled in each stage
decouple_stages = defaultdict(list)
for part,info in parts_info.items():
    decouple_stages[info['decouple_stage']].append(part)

# Get parts activated in each stage
stages = defaultdict(list)
for part,info in parts_info.items():
    stages[info['stage']].append(part)

# Merge adjacent stages that do not decouple any parts (ignoring launch clamps)
for stage in range(max(stages.keys()), 0, -1):
    if stage in stages:
        if len(filter(lambda p: p.launch_clamp is None, decouple_stages[stage])) == 0 and \
           len(filter(lambda p: p.launch_clamp is None, decouple_stages[stage-1])) == 0:
            stages[stage-1].extend(stages[stage])
            del stages[stage]

# Information about engines
engines_info = {}

# Compute information about fuel tanks
tanks_info = {}
for part,info in parts_info.items():
    if len(info['resources']) > 0:
        tanks_info[part] = {}
        for propellant in info['resources']:
            tanks_info[part][propellant] = {
                'mass': part.resources.amount(propellant) * density[propellant],
                'flow_rate': 0
            }

# Helpers to output table
def output_row(cells):
    print ' | '.join('% 10s' % x for x in cells)
def output_divider(ncells):
    print '-+-' . join(['-'*10] * ncells)

# Output headings for table
cols = ('Stage', 'Time', 'Mass', 'Dry Mass', 'Isp', 'Delta-V', 'TWR')
output_row(cols)
output_divider(len(cols))

# Compute delta-v for each stage
total_delta_v = 0
for stage,parts in sorted(stages.items(), key=lambda (k,v): -k):

    # Remove jettisoned parts
    for part in decouple_stages[stage]:
        if part in tanks_info:
            del tanks_info[part]
        engine = parts_info[part]['engine']
        if engine is not None and engine in engines_info:
            del engines_info[engine]

    #print stage
    #print 'activate'
    #for p in parts:
    #    print '  ', p, p.title
    #print 'decouple'
    #for p in decouple_stages[stage]:
    #    print '  ', p, p.title

    for part in decouple_stages[stage]:
        if part in parts:
            parts.remove(part)
            #print 'remove ', part, part.title

    # Compute total mass of stage (all parts plus starting fuel)
    stage_total_mass = 0
    for _,stage_parts in filter(lambda (k,v): k < stage, decouple_stages.items()):
        for part in stage_parts:
            if part in tanks_info:
                stage_total_mass += parts_info[part]['dry_mass']
                for propellant,info in tanks_info[part].items():
                    stage_total_mass += info['mass']
            else:
                stage_total_mass += parts_info[part]['mass']

    # Compute information about newly activated engines
    engines = filter(None, [parts_info[p]['engine'] for p in parts])
    for engine in engines:
        thrust = engine.max_thrust * engine.thrust_limit
        isp = engine.vacuum_specific_impulse
        flow_rate = thrust / (isp * 9.82)
        engines_info[engine] = {
            'part': engine.part,
            'thrust': thrust,
            'isp': isp,
            'flow_rate': flow_rate,
            'tanks': {},
            'propellants': [str(x) for x in engine.propellants] #TODO: fix str -> unicode bug
        }

    # Loop until an engine in this stage flames out
    stage_burn_time = 0
    while len(engines_info) > 0:

        ttime = 0

        # For each engine, find the fuel tank(s) from which it will currently take fuel
        # http://forum.kerbalspaceprogram.com/threads/64362-Fuel-Flow-Rules-%280-24-2%29
        for engine,engine_info in engines_info.items():
            #TODO: support more engine types
            # SRB is its own fuel tank
            if 'SolidFuel' in engine_info['propellants']:
                part = engine_info['part']
                tanks = []
                if tanks_info[part]['SolidFuel']['mass'] > 0.1:
                    tanks = [part]
                engine_info['tanks']['SolidFuel'] = tanks
            # Find tank that LFO rockets are currently consuming
            else:
                for propellant in engine_info['propellants']:
                    visited = set()
                    # TODO: recursive algorithm, could be made iterative
                    def find_tanks(root_part, propellant):

                        # Rule 1
                        if root_part in visited:
                            return []
                        visited.add(root_part)

                        # Rule 2
                        tanks = []
                        parts = parts_info[root_part]['fuel_lines_from']
                        for part in parts:
                            tanks.extend(find_tanks(part, propellant))
                        if len(tanks) > 0:
                            return tanks

                        # Rule 4
                        if parts_info[root_part]['crossfeed']:
                            parts = filter(lambda p: parts_info[p]['axially_attached'],
                                           parts_info[root_part]['children'])
                            if parts_info[root_part]['parent'] is not None and \
                               parts_info[root_part]['axially_attached']:
                                parts.append(parts_info[root_part]['parent'])
                            tanks = []
                            for part in parts:
                                tanks.extend(find_tanks(part, propellant))
                            if len(tanks) > 0:
                                return tanks

                        # Rule 5
                        if root_part in tanks_info:
                            info = tanks_info[root_part]
                            if propellant in info  and info[propellant]['mass'] > 0.1:
                                return [root_part]

                        # Rule 6
                        if root_part in tanks_info:
                            info = tanks_info[root_part]
                            if propellant in info and info[propellant]['mass'] < 0.1:
                                return []

                        # TODO: fuel is not supposed to flow radially though?!
                        # Rule 7
                        #if root_part.crossfeed and \
                        #   root_part.parent is not None and \
                        #   root_part.radially_attached:
                        #    return find_tanks(root_part.parent, propellant)

                        # Rule 8
                        return []

                    tanks = find_tanks(engine_info['part'], propellant)
                    engine_info['tanks'][propellant] = tanks

        # If an engine has flamed out, activate the next stage
        flameout = False
        for engine,engine_info in engines_info.items():
            for propellant in engine_info['propellants']:
                if propellant not in engine_info['tanks'] or len(engine_info['tanks'][propellant]) == 0:
                    flameout = True
                    break
            if flameout:
                break
        if flameout:
            break

        # Calculate the rate at which fuel is flowing out of each tank
        for part,info in tanks_info.items():
            for propellant in info.keys():
                info[propellant]['flow_rate'] = 0
        for engine,engine_info in engines_info.items():
            # Engines consume fuel from each connected tank evenly
            # Ratio of Liquid to Ox is 9:11
            # TODO: get the ratio from KSP
            # TODO: support more types of engine
            if 'SolidFuel' in engine_info['propellants']:
                tank_info = tanks_info[engine_info['part']]['SolidFuel']
                tank_info['flow_rate'] = engine_info['flow_rate']
            else:
                for propellant in engine_info['propellants']:
                    if propellant == 'LiquidFuel':
                        ratio = 9./(9.+11.)
                    else: # TODO: assumes Oxidizer
                        ratio = 11./(9.+11.)
                    tanks = engine_info['tanks'][propellant]
                    ratio /= float(len(tanks))
                    flow_rate_per_tank = engine_info['flow_rate'] * ratio
                    for tank in tanks:
                        tanks_info[tank][propellant]['flow_rate'] += flow_rate_per_tank

        # Compute minimum time to empty any of the tanks
        burn_time = float('inf')
        for tank,tank_info in tanks_info.items():
            for propellant,data in tank_info.items():
                if data['flow_rate'] > 0:
                    burn_time = min(burn_time, data['mass'] / data['flow_rate'])

        # Simulate the burn until the first tank is empty
        for tank, tank_info in tanks_info.items():
            for propellant,data in tank_info.items():
                if data['flow_rate'] > 0:
                    data['mass'] -= data['flow_rate'] * burn_time

        stage_burn_time += burn_time

    # Compute dry mass of stage (all parts plus remaining fuel)
    stage_dry_mass = 0
    for _,stage_parts in filter(lambda (k,v): k < stage, decouple_stages.items()):
        for part in stage_parts:
            if part in tanks_info:
                stage_dry_mass += parts_info[part]['dry_mass']
                for propellant,info in tanks_info[part].items():
                    stage_dry_mass += info['mass']
            else:
                stage_dry_mass += parts_info[part]['mass']

    # Compute combined Isp of engines active in this stage
    thrust = sum(info['thrust'] for info in engines_info.values())
    fuel_flow = sum(info['thrust'] / info['isp'] for info in engines_info.values())
    stage_isp = 0
    if fuel_flow > 0:
        stage_isp = thrust / fuel_flow

    # Compute Delta-V
    stage_delta_v = stage_isp * 9.82 * math.log(stage_total_mass / stage_dry_mass)
    total_delta_v += stage_delta_v

    # Compute TWR
    weight = stage_total_mass * 9.82
    stage_twr = thrust / weight

    if stage_delta_v > 0:
        output_row(('%d' % stage, '%d s' % stage_burn_time,
                    '%.1f t' % (stage_total_mass/1000.), '%.1f t' % (stage_dry_mass/1000.),
                    '%d s' % stage_isp, '%d m/s' % stage_delta_v, '%.2f' % stage_twr))

output_row(('Total', '', '', '', '', '%d m/s' % total_delta_v, ''))

import krpc, curses, time, sys
import numpy as np
import numpy.linalg as la

# Set up curses
stdscr = curses.initscr()
curses.nocbreak()
stdscr.keypad(1)
curses.noecho()

try:

    # Connect to kRPC
    conn = krpc.connect(name='Control Display')
    control = conn.space_center.active_vessel.control

    pitch = conn.add_stream(getattr, control, 'pitch')
    yaw = conn.add_stream(getattr, control, 'yaw')
    roll = conn.add_stream(getattr, control, 'roll')
    throttle = conn.add_stream(getattr, control, 'throttle')
    sas = conn.add_stream(getattr, control, 'sas')
    sas_mode = conn.add_stream(getattr, control, 'sas_mode')
    rcs = conn.add_stream(getattr, control, 'rcs')

    while True:

        stdscr.clear()
        stdscr.addstr(0,0,'-- Controls --')

        if sas():
            sas_text = 'SAS enabled (%s)' % str(sas_mode()).split('.')[1]
        else:
            sas_text = 'SAS disabled'
        if rcs():
            rcs_text = 'RCS enabled'
        else:
            rcs_text = 'RCS disabled'

        # Output information
        stdscr.addstr(2,0,'Pitch: {:+6.3f}'.format(pitch()))
        stdscr.addstr(3,0,'Yaw:   {:+6.3f}'.format(yaw()))
        stdscr.addstr(4,0,'Roll:  {:+6.3f}'.format(roll()))
        stdscr.addstr(5,0,'Throttle: {:>3.0f}%'.format(throttle()*100.0))
        stdscr.addstr(6,0,sas_text)
        stdscr.addstr(7,0,rcs_text)

        stdscr.refresh()
        time.sleep(0.1)

finally:
    # Shutdown curses
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

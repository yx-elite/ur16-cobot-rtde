import sys
sys.path.append("..")
import logging
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config
import time


# logging.basicConfig(level=logging.INFO)

ROBOT_HOST = '192.168.189.129'
ROBOT_PORT = 30004
config_filename = 'data-logging-config.xml'

keep_running = True

logging.getLogger().setLevel(logging.INFO)

conf = rtde_config.ConfigFile(config_filename)
state_names, state_types = conf.get_recipe("state")
setp_names, setp_types = conf.get_recipe("setp")
watchdog_names, watchdog_types = conf.get_recipe("watchdog")

con = rtde.RTDE(ROBOT_HOST, ROBOT_PORT)
con.connect()

# get controller version
con.get_controller_version()

# setup recipes
con.send_output_setup(state_names, state_types)
setp = con.send_input_setup(setp_names, setp_types)
watchdog = con.send_input_setup(watchdog_names, watchdog_types)

# Setpoints to move the robot to
setp1 = [-0.11999999732554396, -0.48350302919797317, 0.5643574832608138, 1.2054759732018596e-15, 3.109999895095828, 0.03999999910593764]
setp2 = [-0.1199999973424296, -0.6753453624175927, 0.15051514995399318, -1.2743603145272124e-14, 3.109999895095813, 0.03999999910596153]

setp.input_double_register_0 = 0
setp.input_double_register_1 = 0
setp.input_double_register_2 = 0
setp.input_double_register_3 = 0
setp.input_double_register_4 = 0
setp.input_double_register_5 = 0

# The function "rtde_set_watchdog" in the "rtde_control_loop.urp" creates a 1 Hz watchdog
watchdog.input_int_register_0 = 0


def setp_to_list(sp):
    sp_list = []
    for i in range(0, 6):
        sp_list.append(sp.__dict__["input_double_register_%i" % i])
    return sp_list


def list_to_setp(sp, list):
    for i in range(0, 6):
        sp.__dict__["input_double_register_%i" % i] = list[i]
    return sp


# start data synchronization
if not con.send_start():
    sys.exit()

# Initialise plotting parameters
# fx, fy, fz, frx, fry, frz = [], [], [], [], [], []
# plot_time = []

# control loop
repetition_counter = 0
repetition = 10
move_completed = True

while keep_running:
    if repetition_counter < repetition:
        # receive the current state
        state = con.receive()

        if state is None:
            break

        # do something...
        if move_completed and state.output_int_register_0 == 1:
            move_completed = False
            new_setp = setp1 if setp_to_list(setp) == setp2 else setp2
            list_to_setp(setp, new_setp)
            print("New pose = " + str(new_setp))
            # send new setpoint
            con.send(setp)
            watchdog.input_int_register_0 = 1
        elif not move_completed and state.output_int_register_0 == 0:
            print("Move to confirmed pose = " + str(state.target_q))
            move_completed = True
            watchdog.input_int_register_0 = 0
            # Data returned from cobot
            tcp_pose = state.actual_TCP_pose
            tcp_force = state.actual_TCP_force
            print(f"Current pose = {tcp_pose}")
            print(f"Current force = {tcp_force}")
            # Two motion in one repetition
            repetition_counter += 0.5
            print(repetition_counter)
            # Take care of movement delay
            time.sleep(1)

        # kick watchdog
        con.send(watchdog)
    else:
        break

print('---------------------------------------------')
print(f'{repetition} repetitions are completed successfully!')

con.send_pause()

con.disconnect()
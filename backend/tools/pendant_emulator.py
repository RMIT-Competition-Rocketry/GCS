import sys
import threading
import termios
from pynput import keyboard
import backend.tools.device_emulator as device_emulator
import backend.process_logging as slogger
from backend.config import load_config
import backend.ansci as ansci
import os
import zmq
import time
import subprocess


THIS_PID: str = str(os.getpid())

KEY_MAP = {
    "SELECTION_TOGGLE_GAS": "1",
    "SELECTION_TOGGLE_IGNITION": "9",
    "GAS_DEADMAN": "g",
    "SELECTION_ROTARY_PURGE": "p",
    "SELECTION_ROTARY_N2O": "n",
    "SELECTION_ROTARY_O2": "o",
    "SELECTION_ROTARY_NEUTRAL": "z",
    "IGNITION_DEADMAN": "d",
    "IGNITION_FIRE": "l",
    "TOGGLE_SYSTEM_ACTIVE": keyboard.Key.enter,
}
# Used for printing names
KEY_MAP_INVERSE = {v: k for k, v in KEY_MAP.items()}

LOCK_FILE_GSE_RESPONSE_PATH: str = \
    load_config()["locks"]["lock_file_gse_response_path"]

gas_rotary_state = None
gas_ignition_switch_state = None
pressed_states = {key: False for key in KEY_MAP.values()}

stop_event = threading.Event()
state_lock = threading.Lock()


def disable_echo():
    fd = sys.stdin.fileno()
    if not sys.stdin.isatty():
        return
    old_settings = termios.tcgetattr(fd)
    new_settings = termios.tcgetattr(fd)
    new_settings[3] = new_settings[3] & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
    return old_settings


def restore_echo(old_settings):
    fd = sys.stdin.fileno()
    if not sys.stdin.isatty():
        return
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def on_press(key):
    with state_lock:
        try:
            char = key.char
            if char in pressed_states and not pressed_states[char]:
                pressed_states[char] = True
                slogger.debug(f'Key {KEY_MAP_INVERSE[char]} pressed')
        except (AttributeError):
            if key in pressed_states and not pressed_states[key]:
                pressed_states[key] = True
                slogger.debug(f'Special Key {KEY_MAP_INVERSE[key]} pressed')


def on_release(key):
    with state_lock:
        try:
            char = key.char
            if char in pressed_states:
                pressed_states[char] = False
                slogger.debug(f'Key {KEY_MAP_INVERSE[char]} released')
        except (AttributeError):
            if key in pressed_states:
                pressed_states[key] = False
                slogger.debug(f'Special Key {KEY_MAP_INVERSE[key]} released')


def calculate_states():
    with state_lock:
        rotary_values = [pressed_states[KEY_MAP['SELECTION_ROTARY_PURGE']],
                         pressed_states[KEY_MAP['SELECTION_ROTARY_O2']],
                         pressed_states[KEY_MAP['SELECTION_ROTARY_N2O']],
                         pressed_states[KEY_MAP['SELECTION_ROTARY_PURGE']]]
        switch_values = [pressed_states[KEY_MAP['SELECTION_TOGGLE_GAS']],
                         pressed_states[KEY_MAP['SELECTION_TOGGLE_IGNITION']]]

        if rotary_values.count(True) > 1:
            raise ValueError(
                "More than one rotary switch is active: " + str(pressed_states))
        if switch_values.count(True) > 1:
            raise ValueError(
                "More than one switch active: " + str(pressed_states))

        GAS_DM = pressed_states[KEY_MAP['GAS_DEADMAN']]
        GAS_SEL = pressed_states[KEY_MAP['SELECTION_TOGGLE_GAS']]

        # GAS_GO = GAS_DM and GAS_SEL
        IGNITION_DM = pressed_states[KEY_MAP['IGNITION_DEADMAN']]
        IGNITION_SEL = pressed_states[KEY_MAP['SELECTION_TOGGLE_IGNITION']]

        states = {
            "MANUAL_PURGE": GAS_DM and pressed_states[KEY_MAP['SELECTION_ROTARY_PURGE']],
            "O2_FILL_ACTIVATE": GAS_DM and pressed_states[KEY_MAP['SELECTION_ROTARY_O2']],
            "SELECTOR_SWITCH_NEUTRAL_POSITION": GAS_DM and pressed_states[KEY_MAP['SELECTION_ROTARY_NEUTRAL']],
            "N2O_FILL_ACTIVATE": GAS_DM and pressed_states[KEY_MAP['SELECTION_ROTARY_N2O']],
            "IGNITION_FIRE": IGNITION_DM and pressed_states[KEY_MAP['IGNITION_FIRE']],
            "IGNITION_SELECTED": IGNITION_SEL,
            "GAS_FILL_SELECTED": GAS_SEL,
            "SYSTEM_ACTIVATE": pressed_states[KEY_MAP['TOGGLE_SYSTEM_ACTIVE']],
        }

        if any(x is None for x in states.values()):
            raise ValueError("Some states are not set: " + str(states))
        return states


def create_lock(LOCK_PATH: str) -> bool:
    if os.path.exists(LOCK_PATH):
        slogger.error(f"Lock file {LOCK_PATH} already exists")
        return False
    with open(LOCK_PATH, "w") as f:
        f.write(THIS_PID)
    slogger.info(f"Lock file created by PID {THIS_PID}")
    return True


def release_lock(LOCK_PATH: str) -> bool:
    if os.path.exists(LOCK_PATH):
        slogger.error(f"Lock file {LOCK_PATH} already exists")
        return False
    with open(LOCK_PATH, "w") as f:
        f.write(THIS_PID)
    slogger.info(f"Lock file created by PID {THIS_PID}")
    return True


def send_packet() -> device_emulator.GCStoGSEStateCMD:
    context = zmq.Context()
    push_socket = context.socket(zmq.PUSH)
    push_socket.connect(
        f"ipc://{os.path.abspath(os.path.join(os.path.sep,'tmp','gcs_rcoket_pull.sock'))}")
    # How long do you wait until you assume the response is not coming and you try again?
    LOCK_TIMEOUT_NS = 6e+8  # 600ms
    # Query user to initialise keyboard library and bypass security
    old_settings = disable_echo()
    while not stop_event.is_set():
        state_command = device_emulator.GCStoGSEStateCMD(**calculate_states())
        payload = state_command.get_payload_bytes()
        push_socket.send(payload)
        create_lock(LOCK_FILE_GSE_RESPONSE_PATH)
        lock_creation_time = time.monotonic_ns()
        # Wait for the lock file to be removed by event viewer
        while os.path.exists(LOCK_FILE_GSE_RESPONSE_PATH):
            if time.monotonic_ns() - lock_creation_time >= LOCK_TIMEOUT_NS:
                # slogger.warning("GSE response timeout. Sending another packet")
                release_lock(LOCK_FILE_GSE_RESPONSE_PATH)
            time.sleep(0.05)


def main():
    device_emulator.MockPacket.initialize_settings(load_config()['emulation'])
    slogger.debug("Starting pendant emulator")
    try:
        # Run packet constructor in a separate thread
        packet_constructor = threading.Thread(target=send_packet)
        packet_constructor.start()
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        slogger.info("Keyboard interrupt received")
        stop_event.set()
        packet_constructor.join()

    finally:
        if old_settings:
            restore_echo(old_settings)


if __name__ == "__main__":
    main()

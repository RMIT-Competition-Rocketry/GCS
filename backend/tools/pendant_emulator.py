import threading
import backend.tools.device_emulator as device_emulator
import backend.process_logging as slogger
from backend.config import load_config
import backend.ansci as ansci
import os
import zmq
import time
import pygame
from typing import Optional, Dict, Union, List


# For those who come back to this code.
# For those who come back to this code.
# For those who come back to this code.
# For those who come back to this code.
# ------------------------------------
# This code was written with little to no planning.
# It was also written with changing requirements in a short amount of time
# There are a hundred better ways to do this, but I just had to rush it asap
# I understand it's terrible :)
# ------------------------------------
# For those who come back to this code.
# For those who come back to this code.
# For those who come back to this code.
# For those who come back to this code.

THIS_PID: str = str(os.getpid())

CONTROLLER_MAP = {
    "BTN_A": 0,
    "BTN_B": 1,
    "BTN_X": 2,
    "BTN_Y": 3,
    "BTN_LB": 4,
    "BTN_RB": 5,
    "BTN_BACK": 6,
    "BTN_START": 7,
    "BTN_LOGITECH": 8,
    "BTN_LEFT_JOYSTICK": 9,
    "BTN_RIGHT_JOYSTICK": 10
}

# Mapped as (button_name, is_momentary)
# If this needs any more information make it an object
KEY_MAP = {
    "SELECTION_TOGGLE_GAS": ("BTN_LEFT_JOYSTICK", False),
    "SELECTION_TOGGLE_IGNITION": ("BTN_RIGHT_JOYSTICK", False),
    "GAS_DEADMAN": ("BTN_LB", True),
    "SELECTION_ROTARY_PURGE": ("BTN_LOGITECH", False),
    "SELECTION_ROTARY_N2O": ("BTN_X", False),
    "SELECTION_ROTARY_O2": ("BTN_B", False),
    "SELECTION_ROTARY_NEUTRAL": ("BTN_BACK", False),
    "IGNITION_DEADMAN": ("BTN_RB", True),
    "IGNITION_FIRE": ("BTN_A", True),
    "TOGGLE_SYSTEM_ACTIVE": ("BTN_START", False),
}

# Check map names match


def validate_maps():
    key_map_values = KEY_MAP.values()
    key_map_values_btn_names = [x[0] for x in key_map_values]
    # Assert: No duplicate or missing button names
    assert len(key_map_values) == len(set(key_map_values_btn_names))
    # Assert: Type check 1
    assert all(isinstance(x[0], str) for x in key_map_values)
    # Assert: Type check 2
    assert all(isinstance(x[1], bool) for x in key_map_values)
    # Assert: Size 2 tuple
    assert all(len(x) == 2 for x in key_map_values)


validate_maps()

# Used for printing names
# 'BTN_??': SELECTGION_TOGGLE_GAS???
KEY_MAP_INVERSE = {v[0]: k for k, v in KEY_MAP.items()}
# fml again
BTN_TOGGLE_MAP = {v[0]: v[1] for v in KEY_MAP.values()}

LOCK_FILE_GSE_RESPONSE_PATH: str = load_config(
)["locks"]["lock_file_gse_response_path"]

pressed_states = {button: False for button in CONTROLLER_MAP.keys()}
pressed_states[KEY_MAP["SELECTION_ROTARY_NEUTRAL"][0]] = True
pressed_states[KEY_MAP["SELECTION_TOGGLE_GAS"][0]] = True

stop_event = threading.Event()
state_lock = threading.Lock()


def setup_controller() -> Optional[pygame.joystick.JoystickType]:
    pygame.init()
    pygame.joystick.init()

    # Attempt controller connection
    if pygame.joystick.get_count() == 0:
        slogger.warning("NO CONTROLLER DETECTED. Defaulting to neutral packet")
        return None

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    if joystick.get_name() != "Logitech Gamepad F710":
        slogger.error(
            f"Invalid controller detected. Please use F710 controller. Found: {joystick.get_name()}")
        raise RuntimeError("Invalid controller type")

    slogger.info(f"Controller initialized: {joystick.get_name()}")
    return joystick


def print_information():
    """Prints information about current states to help the user understand where they're at"""
    # Do no validate information here. That is done in packet sender and on GSE
    if not validate_states():
        # If states are invalid, don't bother printing them.
        # Only print last valid option because invalid packets aren't sent anyway
        return
    with state_lock:
        ON: bool = pressed_states[KEY_MAP['TOGGLE_SYSTEM_ACTIVE'][0]]
        SYSTEM_ACTIVE: str = ansci.BG_GREEN + "ON " if ON else ansci.BG_RED+"OFF"
        SYSTEM_ACTIVE += ansci.RESET
        # Check invalid SPDT state
        if not pressed_states[KEY_MAP['SELECTION_TOGGLE_GAS'][0]] != pressed_states[KEY_MAP['SELECTION_TOGGLE_IGNITION'][0]]:
            IGNITION_GAS_MODE: str = ansci.BG_RED + "XXXXXXXX" + ansci.RESET
            IGNITION_GAS_MODE_NO_COL = "XXXXXXXX"
        else:
            IGNITION_GAS_MODE: str = "GAS     " if pressed_states[
                KEY_MAP['SELECTION_TOGGLE_GAS'][0]] else "IGNITION"
            IGNITION_GAS_MODE_NO_COL = IGNITION_GAS_MODE.strip()
            IGNITION_GAS_MODE = ansci.BG_BLUE + \
                ansci.FG_WHITE + IGNITION_GAS_MODE + ansci.RESET
        # Check invalid rotary states
        ROTRAY_KEYS: List[str] = [
            'SELECTION_ROTARY_PURGE',
            'SELECTION_ROTARY_N2O',
            'SELECTION_ROTARY_O2',
            'SELECTION_ROTARY_NEUTRAL',
        ]
        ROTARY_VALUES = [pressed_states[KEY_MAP[x][0]] for x in ROTRAY_KEYS]
        if ROTARY_VALUES.count(True) != 1:
            ROTARY_STATE: str = ansci.BG_RED + "XXXXXXX" + ansci.RESET
        else:
            for key in ROTRAY_KEYS:
                if pressed_states[KEY_MAP[key][0]]:
                    # hard code for lyf
                    # this file is all temp tho
                    ROTARY_STATE = key[17:].ljust(7, ' ')
                    ROTARY_STATE_NO_COL = ROTARY_STATE.strip()
                    ROTARY_STATE = ansci.BG_MAGENTA + ROTARY_STATE + ansci.RESET
                    break
        # Filling state
        GAS_DM = pressed_states[KEY_MAP['GAS_DEADMAN'][0]]
        FILLING: bool = GAS_DM and ON and IGNITION_GAS_MODE_NO_COL == 'GAS' and ROTARY_STATE_NO_COL in [
            "N2O", "O2"]
        # print(f"Firing: {FIRING}")
        # Firing state
        IGNITION_DM = pressed_states[KEY_MAP['IGNITION_DEADMAN'][0]]
        FIRING: bool = IGNITION_DM and ON and IGNITION_GAS_MODE_NO_COL == 'IGNITION' and pressed_states[
            KEY_MAP['IGNITION_FIRE'][0]]

    ACTION = "FILLING " + \
        ROTARY_STATE_NO_COL if FILLING else "FIRING" if FIRING else "UNDEFINED"
    print(
        f"SYS:{SYSTEM_ACTIVE}|MODE:{IGNITION_GAS_MODE}|ROT:{ROTARY_STATE}|NOTES:{ACTION}")


def handle_controller_events(joystick: Optional[pygame.joystick.JoystickType]):
    clock = pygame.time.Clock()
    if joystick is None:
        # Set nothing default state
        with state_lock:
            pressed_states[KEY_MAP["TOGGLE_SYSTEM_ACTIVE"][0]] = True
            pressed_states[KEY_MAP["SELECTION_ROTARY_NEUTRAL"][0]] = True
            pressed_states[KEY_MAP["SELECTION_TOGGLE_GAS"][0]] = True

    while not stop_event.is_set():
        if joystick is not None:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    handle_button_press(event.button, True)
                elif event.type == pygame.JOYBUTTONUP:
                    handle_button_press(event.button, False)
        clock.tick(60)  # 60 FPS
        # Run CLI notifications
        print_information()


def handle_button_press(button_id, pressed):
    global pressed_states
    button_name = None
    for name, btn_id in CONTROLLER_MAP.items():
        if btn_id == button_id:
            button_name = name
            break

    if button_name and button_name in pressed_states:
        with state_lock:
            action = None
            try:
                toggle_state = BTN_TOGGLE_MAP[button_name]
            except KeyError:
                # Pressed an unmpapped button
                return
            if toggle_state == False:
                # This is a toggle switch
                if pressed:
                    # Only operate this on a press, not on a release
                    if KEY_MAP_INVERSE[button_name] == "TOGGLE_SYSTEM_ACTIVE":
                        # Repeated press toggle logic for SPST
                        pressed_states[button_name] = not pressed_states[button_name]
                    else:
                        # Set state to true, set others to false logic. for non SPST
                        pressed_states[button_name] = True
                    action = "toggled " + \
                        ("on" if pressed_states[button_name] else "off")
                    # Now if you operated on the SPDT, or rotary, you need to turn off the other options
                    # A SPST switch doesn't need this because it only has one state
                    SPDT_options = [KEY_MAP["SELECTION_TOGGLE_GAS"][0],
                                    KEY_MAP["SELECTION_TOGGLE_IGNITION"][0]]
                    if button_name in SPDT_options:
                        SPDT_options.remove(button_name)
                        pressed_states[SPDT_options[0]] = False
                    rotary_options = [KEY_MAP["SELECTION_ROTARY_PURGE"][0],
                                      KEY_MAP["SELECTION_ROTARY_N2O"][0],
                                      KEY_MAP["SELECTION_ROTARY_O2"][0],
                                      KEY_MAP["SELECTION_ROTARY_NEUTRAL"][0]]
                    if button_name in rotary_options:
                        rotary_options.remove(button_name)
                        for reminaing_option in rotary_options:
                            pressed_states[reminaing_option] = False
            else:
                # This is a momentary button
                pressed_states[button_name] = pressed
                action = "pressed" if pressed else "released"

            # if action is not None: slogger.debug(f"Controller {button_name} {action}")


def validate_states():
    """Check if states are ok. This is called in state lock when creating packets. Please be careful not to deadlock"""
    rotary_values = [
        pressed_states[KEY_MAP['SELECTION_ROTARY_PURGE'][0]],
        pressed_states[KEY_MAP['SELECTION_ROTARY_O2'][0]],
        pressed_states[KEY_MAP['SELECTION_ROTARY_N2O'][0]],
        pressed_states[KEY_MAP['SELECTION_ROTARY_NEUTRAL'][0]],
    ]

    switch_values = [
        pressed_states[KEY_MAP['SELECTION_TOGGLE_GAS'][0]],
        pressed_states[KEY_MAP['SELECTION_TOGGLE_IGNITION'][0]]
    ]

    # Validate input states. Check for physically impossible states
    # Don't send packet if in invalid state

    error_present = False  # Check all errors and return at the end
    # An SPDT switch output must be XOR checked
    if not pressed_states[KEY_MAP['SELECTION_TOGGLE_GAS'][0]] != pressed_states[KEY_MAP['SELECTION_TOGGLE_IGNITION'][0]]:
        # slogger.error(f"Selected both gas/ignition state.")
        error_present = True
    # Rotray switch must have only 1 active state
    if not rotary_values.count(True) == 1:
        # slogger.error(f"Only 1 rotary value should be active. Getting: {rotary_values}")
        # pprint(pressed_states)
        error_present = True
    # SPDT switch must have only 1 active state
    if not switch_values.count(True) == 1:
        # slogger.error(f"Only 1 switch should be active")
        # pprint(pressed_states)
        error_present = True

    return not error_present


def calculate_states() -> Union[Dict[str, bool], bool]:
    with state_lock:

        if not validate_states():
            return False

        GAS_DM = pressed_states[KEY_MAP['GAS_DEADMAN'][0]]
        GAS_SEL = pressed_states[KEY_MAP['SELECTION_TOGGLE_GAS'][0]]

        # GAS_GO = GAS_DM and GAS_SEL
        IGNITION_DM = pressed_states[KEY_MAP['IGNITION_DEADMAN'][0]]
        IGNITION_SEL = pressed_states[KEY_MAP['SELECTION_TOGGLE_IGNITION'][0]]

        states = {
            "MANUAL_PURGE": GAS_DM and pressed_states[KEY_MAP['SELECTION_ROTARY_PURGE'][0]],
            "O2_FILL_ACTIVATE": GAS_DM and pressed_states[KEY_MAP['SELECTION_ROTARY_O2'][0]],
            "SELECTOR_SWITCH_NEUTRAL_POSITION": GAS_DM and pressed_states[KEY_MAP['SELECTION_ROTARY_NEUTRAL'][0]],
            "N2O_FILL_ACTIVATE": GAS_DM and pressed_states[KEY_MAP['SELECTION_ROTARY_N2O'][0]],
            "IGNITION_FIRE": IGNITION_DM and pressed_states[KEY_MAP['IGNITION_FIRE'][0]],
            "IGNITION_SELECTED": IGNITION_SEL,
            "GAS_FILL_SELECTED": GAS_SEL,
            "SYSTEM_ACTIVATE": pressed_states[KEY_MAP['TOGGLE_SYSTEM_ACTIVE'][0]],
        }

        # final state validation
        if any(not isinstance(x, bool) for x in states.values()) or len(states) != 8:
            slogger.error(f"Missing/invalid states: {states}")
            return False

        return states


def send_packet() -> device_emulator.GCStoGSEStateCMD:
    context = zmq.Context()
    push_socket = context.socket(zmq.PUSH)
    push_socket.connect(
        f"ipc://{os.path.abspath(os.path.join(os.path.sep, 'tmp', 'gcs_rocket_pendant_pull.sock'))}")

    while not stop_event.is_set():
        states = calculate_states()
        if states == False:
            # Error detected
            slogger.error("Debug error something broken")
            continue
        state_command = device_emulator.GCStoGSEStateCMD(**states)
        push_socket.send(state_command.get_payload_bytes())


def main():
    device_emulator.MockPacket.initialize_settings(load_config()['emulation'])
    slogger.debug("Starting pendant emulator")

    try:
        joystick: Optional[pygame.joystick.JoystickType] = setup_controller()
        packet_thread = threading.Thread(target=send_packet)
        packet_thread.start()
        handle_controller_events(joystick)

    except KeyboardInterrupt:
        slogger.info("Shutting down...")
        stop_event.set()
        packet_thread.join()
        pygame.quit()


if __name__ == "__main__":
    main()

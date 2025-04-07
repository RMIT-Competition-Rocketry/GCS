import threading
import backend.tools.device_emulator as device_emulator
import backend.process_logging as slogger
import config.config as config
import backend.ansci as ansci
from pprint import pprint
import os
import zmq
import time
import pygame
import signal
import enum
from typing import Optional, Dict, Union, Tuple
from functools import cache


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
    "SYSTEM_SELECT_TOGGLE_GAS": ("BTN_LEFT_JOYSTICK", False),
    "SYSTEM_SELECT_TOGGLE_IGNITION": ("BTN_RIGHT_JOYSTICK", False),
    "SYSTEM_SELECT_TOGGLE_NEUTRAL": ("BTN_BACK", False),  # NEW
    "GAS_DEADMAN": ("BTN_LB", True),
    "GAS_SELECTION_ROTARY_PURGE": ("BTN_LOGITECH", False),
    "GAS_SELECTION_ROTARY_N2O": ("BTN_X", False),
    "GAS_SELECTION_ROTARY_NEUTRAL": ("BTN_Y", False),  # CHANGED
    "O2_MOMENTARY": ("BTN_B", True),
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

LOCK_FILE_GSE_RESPONSE_PATH: str = config.load_config(
)["locks"]["lock_file_gse_response_path"]

pressed_states = {button: False for button in CONTROLLER_MAP.keys()}
pressed_states[KEY_MAP["GAS_SELECTION_ROTARY_NEUTRAL"][0]] = True
pressed_states[KEY_MAP["SYSTEM_SELECT_TOGGLE_NEUTRAL"][0]] = True

# Used for change detection
previous_pressed_states = pressed_states.copy()

controller_offline = True

stop_event = threading.Event()
state_lock = threading.Lock()

# Global refference here so it can be cleaned up by signal handler
packet_thread: Optional[threading.Thread] = None


def cleanup_():
    """Internal cleaup code"""
    global packet_thread
    slogger.info("Shutting down...")
    slogger.info("Setting stop event...")
    stop_event.set()
    slogger.info("Stop event set...")
    if packet_thread is not None:
        slogger.info("Packet thread joining...")
        packet_thread.join()
        slogger.info("Packet thread joined...")
    slogger.info("Quitting pygame...")
    pygame.quit()
    slogger.info("Pygame killed. Done...")


def signal_handler(signum, frame):
    """Handles signals like SIGINT (Ctrl+C) and SIGTERM (kill)."""
    slogger.info(f"Received signal {signum}, shutting down...")
    cleanup_()
    os._exit(os.EX_OK)  # Force exit after cleanup


def setup_controller() -> Optional[pygame.joystick.JoystickType]:
    pygame.init()
    pygame.joystick.init()

    # Attempt controller connection
    if pygame.joystick.get_count() == 0:
        slogger.warning("NO CONTROLLER DETECTED. Defaulting to neutral packet")
        return None

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    global controller_offline
    controller_offline = False

    if joystick.get_name() != "Logitech Gamepad F710":
        slogger.error(
            f"Invalid controller detected. Please use F710 controller. Found: {joystick.get_name()}")
        raise RuntimeError("Invalid controller type")

    slogger.info(f"Controller initialized: {joystick.get_name()}")
    return joystick


def print_information():
    class system_selection(enum.Enum):
        GAS = enum.auto()
        IGNITION = enum.auto()
        NEUTRAL = enum.auto()

    class gas_selection(enum.Enum):
        PURGE = enum.auto()
        N20 = enum.auto()
        NEUTRAL = enum.auto()

    def _handle_truth_value(TRUTH_VALUES: Dict[str, bool], COLOUR: str) -> Tuple[str, Union[system_selection, gas_selection]]:
        MAX_VALUE_LENGTH = max(len(x) for x in TRUTH_VALUES.keys())
        if list(TRUTH_VALUES.values()).count(True) > 1:
            slogger.error(
                "Invalid system select state when printing information")
            slogger.debug(TRUTH_VALUES)
            return MAX_VALUE_LENGTH * "X"
        # Return first truth value
        for key, value in TRUTH_VALUES.items():
            if value:
                text = COLOUR + key.ljust(MAX_VALUE_LENGTH, " ") + ansci.RESET
            else:
                continue

            match key:
                case "GAS":
                    enum = system_selection.GAS
                case "IGNITION":
                    enum = system_selection.IGNITION
                case "NEUTRAL":
                    enum = system_selection.NEUTRAL
                case "PURGE":
                    enum = gas_selection.PURGE
                case "N20":
                    enum = gas_selection.N20
                case "NEUTRAL":
                    enum = gas_selection.NEUTRAL
                case _:
                    slogger.error(
                        "Invalid system select state enum when printing information")
            return (text, enum)

    def get_system_select_values() -> Tuple[str, system_selection]:
        TRUTH_VALUES = {
            "GAS": pressed_states[KEY_MAP['SYSTEM_SELECT_TOGGLE_GAS'][0]],
            "IGNITION": pressed_states[KEY_MAP['SYSTEM_SELECT_TOGGLE_IGNITION'][0]],
            "NEUTRAL": pressed_states[KEY_MAP['SYSTEM_SELECT_TOGGLE_NEUTRAL'][0]],
        }
        return _handle_truth_value(TRUTH_VALUES, ansci.BG_YELLOW)

    def get_gas_select_values() -> Tuple[str, gas_selection]:
        TRUTH_VALUES = {
            "PURGE": pressed_states[KEY_MAP['GAS_SELECTION_ROTARY_PURGE'][0]],
            "N20": pressed_states[KEY_MAP['GAS_SELECTION_ROTARY_N2O'][0]],
            "NEUTRAL": pressed_states[KEY_MAP['GAS_SELECTION_ROTARY_NEUTRAL'][0]],
        }
        return _handle_truth_value(TRUTH_VALUES, ansci.BG_MAGENTA)

    def format_on(ON: bool) -> str:
        if ON:
            return ansci.BG_GREEN + "ON " + ansci.RESET
        else:
            return ansci.BG_RED + "OFF" + ansci.RESET

    def gas_information_text(HIGHLIGHT: bool, GAS_FILL_TEXT, GAS_GO: bool) -> str:
        output = ""
        if HIGHLIGHT:
            output += ansci.FG_RED + ansci.BOLD
            output += "FILL TYPE:" + ansci.RESET + GAS_FILL_TEXT
            output += ansci.FG_RED + ansci.BOLD
            output += "GASDM:" + ansci.RESET + ansci.BG_BLUE + ansci.FG_WHITE + \
                ("YES" if GAS_GO else "NO ") + ansci.RESET
        else:
            output += "FILL TYPE:" + ansci.RESET + GAS_FILL_TEXT
            output += "GASDM:" + ansci.RESET + ansci.BG_BLUE + ansci.FG_WHITE + \
                ("YES" if GAS_GO else "NO ") + ansci.RESET
        return output

    def ignition_information_text(HIGHLIGHT: bool, O2_GO: bool, IGNITION_GO: bool) -> str:
        output = ""
        if O2_GO:
            O2_TEXT = ansci.BG_BLACK + ansci.FG_WHITE + "FILL" + ansci.RESET
        else:
            O2_TEXT = ansci.BG_BLACK + "    " + ansci.RESET
        if IGNITION_GO:
            IGNITION_TEXT = ansci.BG_BLACK + ansci.FG_RED + "FIRE" + ansci.RESET
        else:
            IGNITION_TEXT = ansci.BG_BLACK + "    " + ansci.RESET
        if HIGHLIGHT:
            output += ansci.BOLD + ansci.FG_RED
            output += "O2:" + ansci.RESET + ansci.BOLD + O2_TEXT
            output += ansci.BOLD + ansci.FG_RED
            output += "IGNITION:" + ansci.RESET + ansci.BOLD + IGNITION_TEXT
            output += ansci.RESET
        else:
            output += "O2:" + O2_TEXT
            output += "IGNITION:" + IGNITION_TEXT
            output += ansci.RESET
        return output

    def get_final_status_text(ON, GAS_GO, O2_GO, IGNITION_GO,
                              SYSTEM_SELECT: system_selection,
                              GAS_SELECT: gas_selection
                              ) -> str:
        if not ON:
            return "System OFF"
        if SYSTEM_SELECT == system_selection.NEUTRAL:
            return "System Neutral"
        if GAS_GO:
            match GAS_SELECT:
                case gas_selection.PURGE:
                    return "Gas Purging"
                case gas_selection.N20:
                    return "Gas Filling N20"
                case gas_selection.NEUTRAL:
                    return "Gas Neutral Mode"
        if SYSTEM_SELECT == system_selection.IGNITION:
            if O2_GO and not IGNITION_GO:
                return "Filling O2"
            if O2_GO and IGNITION_GO:
                return "Filling O2 & Ignition Firing"
            if not O2_GO and IGNITION_GO:
                return "Ignition Firing"
            if not O2_GO and not IGNITION_GO:
                return "Awiting Ignition Command"

        return "Undefined state"

    """Prints information about current states to help the user understand where they're at"""
    # Do no validate information here. That is done in packet sender and on GSE
    if not validate_switch_states():
        # If states are invalid, don't bother printing them.
        # Only print last valid option because invalid packets aren't sent anyway
        return
    with state_lock:
        # Get logical states for computation
        ON: bool = pressed_states[KEY_MAP['TOGGLE_SYSTEM_ACTIVE'][0]]
        GAS_DM: bool = pressed_states[KEY_MAP['GAS_DEADMAN'][0]]
        IGNITION_DM: bool = pressed_states[KEY_MAP['IGNITION_DEADMAN'][0]]
        IGNITION_FIRE: bool = pressed_states[KEY_MAP['IGNITION_FIRE'][0]]
        O2_MOMENTRAY: bool = pressed_states[KEY_MAP['O2_MOMENTARY'][0]]

        SYSTEM_SELECT_TEXT, SYSTEM_SELECT = get_system_select_values()
        GAS_SELECT_TEXT, GAS_SELECT = get_gas_select_values()
        ON_TEXT: str = format_on(ON)

    print(f"ACTIVE:{ON_TEXT}|SELECT:{SYSTEM_SELECT_TEXT}", end="")
    # Have not printed newline yet. Now add bold and red to variables in scope
    GAS_GO = GAS_DM and ON and SYSTEM_SELECT == system_selection.GAS
    O2_GO = IGNITION_DM and O2_MOMENTRAY and ON and SYSTEM_SELECT == system_selection.IGNITION
    IGNITION_GO = IGNITION_DM and IGNITION_FIRE and ON and SYSTEM_SELECT == system_selection.IGNITION
    match SYSTEM_SELECT:
        case system_selection.GAS:
            print(gas_information_text(True, GAS_SELECT_TEXT, GAS_GO), end="")
            print(ignition_information_text(False, O2_GO, IGNITION_GO), end="")
        case system_selection.IGNITION:
            print(gas_information_text(False, GAS_SELECT_TEXT, GAS_GO), end="")
            print(ignition_information_text(True, O2_GO, IGNITION_GO), end="")
        case system_selection.NEUTRAL:
            print(gas_information_text(False, GAS_SELECT_TEXT, GAS_GO), end="")
            print(ignition_information_text(False, O2_GO, IGNITION_GO), end="")

    print(ansci.BG_GREEN + ansci.FG_BLACK +
          get_final_status_text(
              ON, GAS_GO, O2_GO, IGNITION_GO, SYSTEM_SELECT, GAS_SELECT)
          + ansci.RESET
          )


def handle_controller_events(joystick: Optional[pygame.joystick.JoystickType]):
    global previous_pressed_states, controller_offline
    clock = pygame.time.Clock()
    if joystick is None:
        # Set the (nothing) default state
        with state_lock:
            pressed_states[KEY_MAP["TOGGLE_SYSTEM_ACTIVE"][0]] = False
            pressed_states[KEY_MAP["GAS_SELECTION_ROTARY_NEUTRAL"][0]] = True
            pressed_states[KEY_MAP["SYSTEM_SELECT_TOGGLE_NEUTRAL"][0]] = True
    first_time = True
    firstAddedEvent = True
    while not stop_event.is_set():
        if joystick is not None:
            event = pygame.event.poll()
            if event.type == pygame.NOEVENT:
                continue
            match event.type:
                case pygame.JOYBUTTONDOWN:
                    handle_button_press(event.button, True)
                    # Button event discovered
                    # Use in this block to avoid race conditions
                    controller_offline = False
                case pygame.JOYBUTTONUP:
                    handle_button_press(event.button, False)
                    controller_offline = False
                case pygame.JOYDEVICEREMOVED:
                    slogger.warning("Controller disconnected")
                    controller_offline = True
                case pygame.JOYDEVICEADDED:
                    if not firstAddedEvent:
                        slogger.info(
                            "Controller online. Restart likely required. Maintaining fallback state")
                        controller_offline = True  # This is default behaviour for F710 controller
                        firstAddedEvent = False
        else:
            # Reduce thread load. No need for full speed in testing
            time.sleep(0.05)
        clock.tick(60)  # 60 FPS
        # Run CLI notifications
        if (pressed_states != previous_pressed_states or first_time):
            # Print on change. Many STDOUT ANSCI writes are expensive
            print_information()
            first_time = False
        previous_pressed_states = pressed_states.copy()


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
                    system_rotary_options = [KEY_MAP["SYSTEM_SELECT_TOGGLE_GAS"][0],
                                             KEY_MAP["SYSTEM_SELECT_TOGGLE_IGNITION"][0],
                                             KEY_MAP["SYSTEM_SELECT_TOGGLE_NEUTRAL"][0]]

                    gas_rotary_options = [KEY_MAP["GAS_SELECTION_ROTARY_PURGE"][0],
                                          KEY_MAP["GAS_SELECTION_ROTARY_N2O"][0],
                                          KEY_MAP["GAS_SELECTION_ROTARY_NEUTRAL"][0]]

                    if button_name in gas_rotary_options:
                        gas_rotary_options.remove(button_name)
                        for reminaing_option in gas_rotary_options:
                            pressed_states[reminaing_option] = False

                    if button_name in system_rotary_options:
                        system_rotary_options.remove(button_name)
                        for reminaing_option in system_rotary_options:
                            pressed_states[reminaing_option] = False
            else:
                # This is a momentary button
                pressed_states[button_name] = pressed
                action = "pressed" if pressed else "released"

            # if action is not None: slogger.debug(f"Controller {button_name} {action}")


def validate_switch_states():
    """Check if states are ok. This is called in state lock when creating packets. Please be careful not to deadlock"""
    gas_rotary_values = [
        pressed_states[KEY_MAP['GAS_SELECTION_ROTARY_PURGE'][0]],
        pressed_states[KEY_MAP['GAS_SELECTION_ROTARY_N2O'][0]],
        pressed_states[KEY_MAP['GAS_SELECTION_ROTARY_NEUTRAL'][0]],
    ]

    system_rotary_values = [
        pressed_states[KEY_MAP['SYSTEM_SELECT_TOGGLE_GAS'][0]],
        pressed_states[KEY_MAP['SYSTEM_SELECT_TOGGLE_IGNITION'][0]],
        pressed_states[KEY_MAP['SYSTEM_SELECT_TOGGLE_NEUTRAL'][0]],
    ]

    # Validate input states. Check for physically impossible states
    # Send fallback packet if in invalid state

    error_present = False  # Check all errors and return at the end
    # Rotray switch must have only 1 active state
    if not gas_rotary_values.count(True) == 1:
        slogger.error(
            f"Only 1 gas rotary value should be active. Getting: {gas_rotary_values}")
        pprint(pressed_states)
        error_present = True
    if not system_rotary_values.count(True) == 1:
        slogger.error(
            f"Only 1 system rotary value should be active. Getting: {system_rotary_values}")
        pprint(pressed_states)
        error_present = True

    return not error_present


def calculate_states() -> Union[Dict[str, bool], bool]:
    with state_lock:

        # Check switch states are not impossible
        if not validate_switch_states():
            return False

        SYS_ON = pressed_states[KEY_MAP['TOGGLE_SYSTEM_ACTIVE'][0]]

        # Gas DM is used becuase the rotary switches are spring loaded
        # But our simulation only uses toggle buttons
        GAS_DM = pressed_states[KEY_MAP['GAS_DEADMAN'][0]]
        GAS_SEL = pressed_states[KEY_MAP['SYSTEM_SELECT_TOGGLE_GAS'][0]]

        # GAS_GO = GAS_DM and GAS_SEL
        IGNITION_DM = pressed_states[KEY_MAP['IGNITION_DEADMAN'][0]]
        IGNITION_SEL = pressed_states[KEY_MAP['SYSTEM_SELECT_TOGGLE_IGNITION'][0]]

        # If system is off, the actual pendant GPIO pins will go LOW
        # Enforce electrical GPIO validity based on GPIO layouts
        states = {
            "MANUAL_PURGE": SYS_ON and GAS_SEL and GAS_DM and pressed_states[KEY_MAP['GAS_SELECTION_ROTARY_PURGE'][0]],
            "O2_FILL_ACTIVATE": SYS_ON and IGNITION_SEL and IGNITION_DM and pressed_states[KEY_MAP['O2_MOMENTARY'][0]],
            "SELECTOR_SWITCH_NEUTRAL_POSITION": SYS_ON and GAS_SEL and GAS_DM and pressed_states[KEY_MAP['GAS_SELECTION_ROTARY_NEUTRAL'][0]],
            "N2O_FILL_ACTIVATE": SYS_ON and GAS_SEL and GAS_DM and pressed_states[KEY_MAP['GAS_SELECTION_ROTARY_N2O'][0]],
            "IGNITION_FIRE": SYS_ON and IGNITION_SEL and IGNITION_DM and pressed_states[KEY_MAP['IGNITION_FIRE'][0]],
            "IGNITION_SELECTED": SYS_ON and IGNITION_SEL and IGNITION_DM,
            "GAS_FILL_SELECTED": SYS_ON and GAS_SEL and GAS_DM,
            "SYSTEM_ACTIVATE": SYS_ON,
        }

        # final state validation
        if any(not isinstance(x, bool) for x in states.values()) or len(states) != 8:
            slogger.error(f"Missing/invalid states: {states}")
            return False

        return states


@cache  # Calculate once
def safety_fallback_state():
    """returns the safest state for the GSE to be in.
    Used when a state from the controller cannot be interpreted correctly and we
    still need to send data to GSE to avoid a timeout shutdown

    Leave as function in case logic needs to be updated
    """
    states = {
        "MANUAL_PURGE": False,
        "O2_FILL_ACTIVATE": False,
        "SELECTOR_SWITCH_NEUTRAL_POSITION": False,
        "N2O_FILL_ACTIVATE": False,
        "IGNITION_FIRE": False,
        "IGNITION_SELECTED": False,
        "GAS_FILL_SELECTED": False,
        "SYSTEM_ACTIVATE": False,
    }

    return states


def send_packet() -> device_emulator.GCStoGSEStateCMD:
    context = zmq.Context()
    try:
        push_socket = context.socket(zmq.PUSH)
        SOCKET_PATH = os.path.abspath(os.path.join(
            os.path.sep, 'tmp', 'gcs_rocket_pendant_pull.sock')
        )
        # Wait LINGER_TIME_MS before giving up on push request
        LINGER_TIME_MS = 300
        push_socket.setsockopt(zmq.LINGER, LINGER_TIME_MS)
        push_socket.setsockopt(zmq.SNDHWM, 1)  # Limit send buffer to 1 message
        push_socket.connect(f"ipc://{SOCKET_PATH}")

        while not stop_event.is_set():
            states = calculate_states()
            if states == False or controller_offline:
                # Error detected
                if states == False:
                    slogger.error("Invalid controller state")
                states = safety_fallback_state()
                slogger.warning("In fallback safety state")
            state_command = device_emulator.GCStoGSEStateCMD(**states)
            try:
                push_socket.send(
                    state_command.get_payload_bytes(), flags=zmq.NOBLOCK)
            except zmq.ZMQError:
                # Queue is likely full
                slogger.warning(
                    "ZMQ Push socket is full. Cannot send data until it is emptied in server. Sleeping")
                time.sleep(1)
            # No need to go full blast. Socket will fill up
            time.sleep(0.2)
    finally:
        slogger.debug("Packet sender closing socket")
        push_socket.close()
        slogger.debug("Packet sender closed socket")
        slogger.debug(f"Packet sender closing context (<{LINGER_TIME_MS}ms)")
        context.term()
        slogger.debug("Packet sender thread resources cleaned up")


def main():
    device_emulator.MockPacket.initialize_settings(
        config.load_config()['emulation'])
    slogger.debug("Starting pendant emulator")

    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle `kill` command

    global packet_thread

    try:
        joystick: Optional[pygame.joystick.JoystickType] = setup_controller()
        packet_thread = threading.Thread(target=send_packet)
        packet_thread.start()
        handle_controller_events(joystick)

    except KeyboardInterrupt:
        cleanup_()


if __name__ == "__main__":
    main()

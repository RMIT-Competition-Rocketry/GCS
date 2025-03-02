import sys
import threading
import backend.tools.device_emulator as device_emulator
import backend.process_logging as slogger
from backend.config import load_config
import backend.ansci as ansci
import os
import zmq
import time
import pygame
import json
from typing import Optional, Dict, Union

THIS_PID: str = str(os.getpid())

# Load controller mapping from JSON
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

KEY_MAP = {
    "SELECTION_TOGGLE_GAS": "BTN_LEFT_JOYSTICK",
    "SELECTION_TOGGLE_IGNITION": "BTN_RIGHT_JOYSTICK",
    "GAS_DEADMAN": "BTN_LB",
    "SELECTION_ROTARY_PURGE": "BTN_LOGITECH",
    "SELECTION_ROTARY_N2O": "BTN_X",
    "SELECTION_ROTARY_O2": "BTN_B",
    "SELECTION_ROTARY_NEUTRAL": "BTN_BACK",
    "IGNITION_DEADMAN": "BTN_RB",
    "IGNITION_FIRE": "BTN_A",
    "TOGGLE_SYSTEM_ACTIVE": "BTN_START",
}

# Used for printing names
KEY_MAP_INVERSE = {v: k for k, v in KEY_MAP.items()}

LOCK_FILE_GSE_RESPONSE_PATH: str = load_config()["locks"]["lock_file_gse_response_path"]

pressed_states = {button: False for button in CONTROLLER_MAP.keys()}
stop_event = threading.Event()
state_lock = threading.Lock()

def setup_controller():
    pygame.init()
    pygame.joystick.init()
    
    # Wait for controller connection
    while pygame.joystick.get_count() == 0:
        slogger.debug("Waiting for controller connection...")
        time.sleep(0.5)
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    
    if joystick.get_name() != "Logitech Gamepad F710":
        slogger.error(f"Invalid controller detected. Please use F710 controller. Found: {joystick.get_name()}")
        raise RuntimeError("Invalid controller type")
    
    slogger.info(f"Controller initialized: {joystick.get_name()}")
    return joystick

def handle_controller_events(joystick):
    clock = pygame.time.Clock()
    while not stop_event.is_set():
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                handle_button_press(event.button, True)
            elif event.type == pygame.JOYBUTTONUP:
                handle_button_press(event.button, False)
        clock.tick(60)  # 60 FPS

def handle_button_press(button_id, pressed):
    button_name = None
    for name, btn_id in CONTROLLER_MAP.items():
        if btn_id == button_id:
            button_name = name
            break
    
    if button_name and button_name in pressed_states:
        with state_lock:
            pressed_states[button_name] = pressed
            action = "pressed" if pressed else "released"
            slogger.debug(f"Controller {button_name} {action}")

def calculate_states() -> Union[Dict[str, bool],bool]:
    with state_lock:
        rotary_values = [
            pressed_states[KEY_MAP['SELECTION_ROTARY_PURGE']],
            pressed_states[KEY_MAP['SELECTION_ROTARY_O2']],
            pressed_states[KEY_MAP['SELECTION_ROTARY_N2O']],
            pressed_states[KEY_MAP['SELECTION_ROTARY_PURGE']]
        ]
        
        switch_values = [
            pressed_states[KEY_MAP['SELECTION_TOGGLE_GAS']],
            pressed_states[KEY_MAP['SELECTION_TOGGLE_IGNITION']]
        ]

        # Validate input states
        error_present = False
        if rotary_values.count(True) > 1:
            slogger.error(f"Multiple rotary switches active: {pressed_states}")
            error_present = True
        if switch_values.count(True) > 1:
            slogger.error(f"Multiple switches active: {pressed_states}")
            error_present = True
        
        if error_present:
            return False

        # Calculate final states
        states = {
            "MANUAL_PURGE": pressed_states['BTN_LB'] and pressed_states['BTN_LOGITECH'],
            "O2_FILL_ACTIVATE": pressed_states['BTN_LB'] and pressed_states['BTN_B'],
            "SELECTOR_SWITCH_NEUTRAL_POSITION": pressed_states['BTN_LB'] and pressed_states['BTN_BACK'],
            "N2O_FILL_ACTIVATE": pressed_states['BTN_LB'] and pressed_states['BTN_X'],
            "IGNITION_FIRE": pressed_states['BTN_RB'] and pressed_states['BTN_A'],
            "IGNITION_SELECTED": pressed_states['BTN_RIGHT_JOYSTICK'],
            "GAS_FILL_SELECTED": pressed_states['BTN_LEFT_JOYSTICK'],
            "SYSTEM_ACTIVATE": pressed_states['BTN_START'],
        }

        if any(x is None for x in states.values()):
            slogger.error(f"Missing states: {states}")
            return False
            
        return states

def send_packet() -> device_emulator.GCStoGSEStateCMD:
    context = zmq.Context()
    push_socket = context.socket(zmq.PUSH)
    push_socket.connect(f"ipc://{os.path.abspath(os.path.join(os.path.sep,'tmp','gcs_rcoket_pull.sock'))}")
    
    LOCK_TIMEOUT_NS = 6e8  # 600ms
    while not stop_event.is_set():
        states = calculate_states()
        if states == False: continue # Error detected
        state_command = device_emulator.GCStoGSEStateCMD(**states)
        push_socket.send(state_command.get_payload_bytes())
        
        if create_lock(LOCK_FILE_GSE_RESPONSE_PATH):
            lock_creation_time = time.monotonic_ns()
            while os.path.exists(LOCK_FILE_GSE_RESPONSE_PATH):
                if time.monotonic_ns() - lock_creation_time >= LOCK_TIMEOUT_NS:
                    release_lock(LOCK_FILE_GSE_RESPONSE_PATH)
                time.sleep(0.05)

def create_lock(lock_path: str) -> bool:
    if os.path.exists(lock_path):
        slogger.error(f"Lock file {lock_path} exists")
        return False
    with open(lock_path, "w") as f:
        f.write(THIS_PID)
    # slogger.info(f"Lock created by PID {THIS_PID}")
    return True

def release_lock(lock_path: str) -> bool:
    if not os.path.exists(lock_path):
        slogger.error(f"Lock file {lock_path} missing")
        return False
    os.remove(lock_path)
    return True

def main():
    device_emulator.MockPacket.initialize_settings(load_config()['emulation'])
    slogger.debug("Starting pendant emulator")
    
    try:
        joystick = setup_controller()
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
import zmq
import backend.includes_python.process_logging as slogger
import os
import time
import backend.device_emulator as device_emulator
import backend.includes_python.service_helper as service_helper
import config.config as config
import threading
try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    slogger.error(
        "RPi.GPIO not found, this library is only available on Raspberry Pi devices.")
    # raise NotImplementedError(
    # "Mocking not implemented yet. I don't have enough time right now")

    class GPIOStub:
        BCM = IN = PUD_DOWN = None
        def setmode(self, mode): pass
        def setup(self, pin, mode, pull_up_down=None): pass
        def input(self, pin): return False
        def cleanup(self): pass
    GPIO = GPIOStub()
from abc import ABC, abstractmethod


class StateTable():
    """
    Stores the states (argument) for the GSE to GCS packet. bonza cunt
    """

    FALLBACK_DICT = {
        "SYS_ON": False,
        "FILL_SELECTED": False,
        "IGNITION_SELECTED": False,
        "N2O_ACTIVE": False,
        "NEUTRAL_ACTIVE": False,
        "PURGE_ACTIVE": False,
        "O2_MOMENT_ACTIVE": False,
        "IGNITION_MOMENT_ACTIVE": False,
    }

    @staticmethod
    def _bool_table_str(printable_dict: dict) -> str:
        MAX_KEY_LEN = max(len(str(k)) for k in printable_dict)
        output = ""
        for k, v in printable_dict.items():
            assert isinstance(v, bool)
            symbol = '🟩' if v else '🟥'
            output += f"{k:<{MAX_KEY_LEN}} : {symbol}"
        return output

    def __str__(self):
        mock_states = self.get_states_dict()
        return StateTable._bool_table_str(mock_states)

    def __repr__(self):
        """Debug print statement"""
        debug_attributes = {
            "SYS_ON": self.SYS_ON,
            "FILL_SELECTED": self.FILL_SELECTED,
            "IGNITION_SELECTED": self.IGNITION_SELECTED,
            "N2O_ACTIVE": self.N2O_ACTIVE,
            "NEUTRAL_ACTIVE": self.NEUTRAL_ACTIVE,
            "PURGE_ACTIVE": self.PURGE_ACTIVE,
            "O2_MOMENT_ACTIVE": self.O2_MOMENT_ACTIVE,
            "IGNITION_MOMENT_ACTIVE": self.IGNITION_MOMENT_ACTIVE,
        }
        # Get string of outputs
        output = StateTable._bool_table_str(debug_attributes)
        # Get string if calculated packet states
        output += '\n'
        output += self.__str__()
        return output

    def __init__(self,
                 SYS_ON: bool = True,
                 FILL_SELECTED: bool = True,
                 IGNITION_SELECTED: bool = True,
                 N2O_ACTIVE: bool = True,
                 NEUTRAL_ACTIVE: bool = True,
                 PURGE_ACTIVE: bool = True,
                 O2_MOMENT_ACTIVE: bool = True,
                 IGNITION_MOMENT_ACTIVE: bool = True,
                 ):
        self.SYS_ON = SYS_ON
        self.FILL_SELECTED = FILL_SELECTED
        self.IGNITION_SELECTED = IGNITION_SELECTED
        self.N2O_ACTIVE = N2O_ACTIVE
        self.NEUTRAL_ACTIVE = NEUTRAL_ACTIVE
        self.PURGE_ACTIVE = PURGE_ACTIVE
        self.O2_MOMENT_ACTIVE = O2_MOMENT_ACTIVE
        self.IGNITION_MOMENT_ACTIVE = IGNITION_MOMENT_ACTIVE

    def get_states_dict(self) -> dict:
        """returns argument dictionary for use in GCS to GSE packet
        """
        # You should also check these states electronically where applicable
        states = {
            "MANUAL_PURGE": self.SYS_ON and self.FILL_SELECTED and self.PURGE_ACTIVE,
            "O2_FILL_ACTIVATE": self.SYS_ON and self.IGNITION_SELECTED and self.O2_MOMENT_ACTIVE,
            "SELECTOR_SWITCH_NEUTRAL_POSITION": self.SYS_ON and self.FILL_SELECTED and self.NEUTRAL_ACTIVE,
            "N2O_FILL_ACTIVATE": self.SYS_ON and self.FILL_SELECTED and self.N2O_ACTIVE,
            "IGNITION_FIRE": self.SYS_ON and self.IGNITION_SELECTED and self.IGNITION_MOMENT_ACTIVE,
            "IGNITION_SELECTED": self.SYS_ON and self.IGNITION_SELECTED,
            "GAS_FILL_SELECTED": self.SYS_ON and self.FILL_SELECTED,
            "SYSTEM_ACTIVATE": self.SYS_ON,
        }

        # Type and range validation
        if any(not isinstance(x, bool) for x in states.values()) or len(states) != 8:
            slogger.error(f"Missing/invalid states: {states}")
            return StateTable.get_fallback_table()

        # Nonsensical states that should not exist. GSE will complain if any true
        nonsensical_conditions = {
            "purge and fill": states["MANUAL_PURGE"] and states["O2_FILL_ACTIVATE"],
            "purge on neutral": states["MANUAL_PURGE"] and states["SELECTOR_SWITCH_NEUTRAL_POSITION"],
            # states["MANUAL_PURGE"] and states["SELECTOR_SWITCH_NEUTRAL_POSITION"]
            # add more. please do this automatically
        }

        for k, v in nonsensical_conditions.items():
            if v:
                slogger.warning(f"Impossible condition detected: {k}")
                states = StateTable.FALLBACK_DICT

        return states

    def get_fallback_table() -> dict:
        """Return an instance of StateTable which is safe"""
        return StateTable(**StateTable.FALLBACK_DICT)


class ControlDevice(ABC):
    def __init__(self):
        self._setup_device()
        # Set default fallback state to send whist waiting for inputs
        self.state_table = StateTable.get_fallback_table()

    @abstractmethod
    def _setup_device(self):
        """Setup the control device"""
        pass

    @abstractmethod
    def _update_state_table(self) -> None:
        """Updates state table with new values"""
        pass

    def get_state_table(self) -> StateTable:
        """Updates and gets the current states from the control device."""
        try:
            state_table = None
            state_table = self._update_state_table()
        except Exception:
            slogger.warning("Failed to update pendant states")
        if not state_table:
            slogger.warning(
                "No inputs received from control device, using fallback state")
            state_table = StateTable.get_fallback_table()
        self.state_table = state_table
        return self.state_table

    def cleanup(self):
        """Code to run after controller is no longer needed."""
        pass


class RPI_GPIO_Device(ControlDevice):
    """Parent class for GPIO devices on Raspberry Pi."""
    # MAPPING FROM DB15 PINS
    # PIN1 -> POWER (5V)?
    # DB_PIN_GPIO_0 -> (SYS_ACTIVE)
    # DB_PIN_GPIO_1 -> (FILL_SELECTED)
    # DB_PIN_GPIO_2 -> (IGNITION_SELECTED)
    # DB_PIN_GPIO_3 -> (IGNITION_MOMENT_ACTIVE)
    # DB_PIN_GPIO_4 -> (N2O_ACTIVE)
    # DB_PIN_GPIO_5 -> (NEUTRAL_ACTIVE) *currently unwired*
    # DB_PIN_GPIO_6 -> (O2_MOMENT_ACTIVE)
    # DB_PIN_GPIO_7 -> (PURGE_ACTIVE)
    # PIN9 -> GND

    # What GPIO ports represent the logical input
    PIN_MAP = {
        4: "SYS_ON",
        17: "FILL_SELECTED",
        27: "IGNITION_SELECTED",
        22: "IGNITION_MOMENT_ACTIVE",
        10: "N2O_ACTIVE",
        9: "NEUTRAL_ACTIVE",
        11: "O2_MOMENT_ACTIVE",
        5: "PURGE_ACTIVE",
    }

    def _setup_device(self):
        GPIO.setmode(GPIO.BCM)
        for pin in self.pin_map:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def __init__(self):
        super().__init__()
        self._setup_device()

    def _update_state_table(self):
        """Updates instance attributes and returns a dictionary of the current states."""
        for pin, attr in RPI_GPIO_Device.PIN_MAP.items():
            setattr(self, attr, GPIO.input(pin))
        states = {
            attr: getattr(self, attr) for attr in RPI_GPIO_Device.PIN_MAP.values()
        }
        # Temporary fix for neutral state which isn't wired
        self.NEUTRAL_ACTIVE = not self.N2O_ACTIVE and not self.PURGE_ACTIVE
        self.state_table = StateTable(**states)

    def cleanup(self):
        super().cleanup()
        GPIO.cleanup()


def get_control_device(key: str) -> ControlDevice:
    key = key.lower().strip()
    return {
        'rpi_gpio_device': RPI_GPIO_Device,
    }.get(key, None)


def send_packet():
    context = zmq.Context()
    try:
        push_socket = context.socket(zmq.PUSH)
        CONFIG = config.load_config()
        SOCKET_PATH = os.path.abspath(os.path.join(
            os.path.sep, 'tmp', 'gcs_rocket_pendant_pull.sock')
        )
        CONTROL_TYPE = CONFIG['hardware']['controller']
        controller: ControlDevice = get_control_device(CONTROL_TYPE)
        # Wait LINGER_TIME_MS before giving up on push request
        LINGER_TIME_MS = 300

        push_socket.setsockopt(zmq.LINGER, LINGER_TIME_MS)
        push_socket.setsockopt(zmq.SNDHWM, 1)  # Limit send buffer to 1 message
        push_socket.connect(f"ipc://{SOCKET_PATH}")

        while not service_helper.time_to_stop():
            # Get values to pass to emulator
            # These states are validated, error checked and include fallback
            states = controller.get_state_table()
            state_command = device_emulator.GCStoGSEStateCMD(**states)
            try:
                push_socket.send(
                    state_command.get_payload_bytes(EXTERNAL=True), flags=zmq.NOBLOCK)
            except zmq.ZMQError:
                # Queue is likely full
                slogger.warning(
                    "ZMQ Push socket is full. Cannot send data until it is emptied in server. Sleeping")
                time.sleep(1)
            # No need to go full blast.
            time.sleep(0.05)
    finally:
        slogger.debug("Packet sender closing socket")
        push_socket.close()
        slogger.debug("Packet sender closed socket")
        slogger.debug(f"Packet sender closing context (<{LINGER_TIME_MS}ms)")
        context.term()
        slogger.debug("Packet sender thread resources cleaned up")
        slogger.debug("Cleaning up controller")
        controller.cleanup()
        slogger.debug("Cleaned up controller")


def main():
    device_emulator.MockPacket.initialize_settings(
        config.load_config()['emulation'])
    slogger.debug("Starting pendant emulator")

    # global packet_thread
    # packet_thread = threading.Thread(target=send_packet)
    # packet_thread.start()
    send_packet()


if __name__ == "__main__":
    main()

import logging
import cli.proccess as process
import enum
import os
from typing import Optional


class SimulationType(enum.Enum):
    TEST = "TEST"
    LEGACY = "legacy"
    FAIL = "fail"


def get_available_missions():
    """Scans the mission directory and then returns the available missions"""
    MISSION_PATH = os.path.join("backend", "replay_system", "mission_data")
    if not os.path.exists(MISSION_PATH):
        return []

    return [d for d in os.listdir(MISSION_PATH)
            if os.path.isdir(os.path.join(MISSION_PATH, d))]


def get_mission_path(mission: Optional[str]) -> str:
    """Get the mission path from the command line argument, validation should exist already"""
    MISSION_PATH = os.path.join("backend", "replay_system", "mission_data")

    if mission is None:
        raise ValueError("Mission argument is required")

    FULL_MISSION_PATH = os.path.join(MISSION_PATH, mission)
    valid_missions = get_available_missions()
    if FULL_MISSION_PATH not in valid_missions:
        raise ValueError(
            f"Invalid Mission: {mission}. Valid missions are {', '. join(valid_missions)}"
        )
    return mission


def start_replay_system(logger: logging.Logger, DEVICE: str, MISSION: Optional[str] = None, SIMULATION: Optional[str] = None):
    """Starts the replay system either in simulation mode or mission mode

    Args:
        logger: Logger
        DEVICE: device
        MISSION: Mission directory name
        SIMULATION: Simuation type
    """
    SERVICE_NAME = "replay system"
    try:
        if MISSION and SIMULATION:
            raise ValueError("Can't have both simulation and mission data")

        if not MISSION and not SIMULATION:
            raise ValueError("Must have either mission or simulation type")
        REPLAY_COMMAND = [
            "python3", "-u", os.path.join("backend",
                                          "replay_system", "replay_engine.py"),
            "--device-rocket", DEVICE,
        ]
        if MISSION:
            REPLAY_COMMAND.extend(["--mode", "mission", "--mission", MISSION])
        elif SIMULATION:
            REPLAY_COMMAND.extend(
                ["--mode", "simulation", "--simulation", SIMULATION])

        logger.debug(
            f"Starting {SERVICE_NAME} module with: {REPLAY_COMMAND}"
        )

        # Set up the PYTHONPATH to the project root to ensure the imports will work
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        emulator_process = process.LoggedSubProcess(
            REPLAY_COMMAND,
            name=SERVICE_NAME,
            parse_output=True,
            env=env,
        )
        emulator_process.start()

    except Exception as e:
        logger.error(
            f"An error occured while starting {SERVICE_NAME}: {e}"
        )
        return None, None

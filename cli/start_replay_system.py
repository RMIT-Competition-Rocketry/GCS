import logging
import cli.proccess as process
import enum
import os
from typing import Optional


class MissionType(enum.Enum):
    MISSION1 = "20250504"


def get_mission_type(mission: Optional[str]) -> MissionType:
    """Get the interface type from the command line argument or config"""
    # @TODO do this later
    # if interface is None:  # Unspecified by user
    #     interface = config.load_config(
    #     )['hardware']['interface'].strip().upper()
    # else:
    #     interface = interface.strip().upper()

    # Convert string to MissionType enum
    try:
        for enum_member in MissionType:
            if enum_member.value == mission:
                return enum_member
        # If we get here, no matching enum value was found
        valid_types = [e.name for e in MissionType]
        raise ValueError(
            f"Invalid mission type: '{mission}'. Valid types are: {', '.join(valid_types)}")
    except Exception as e:
        raise ValueError(f"Invalid mission type: {mission}")


def start_replay_system(logger: logging.Logger, DEVICE: str, MISSION_TYPE: MissionType):
    if not isinstance(MISSION_TYPE, MissionType):
        raise ValueError(
            f"MISSION_TYPE must be a MissionType value, got: {MISSION_TYPE} as type {type(MISSION_TYPE)} instead")
        
    if MISSION_ARG != None:
        MISSION_TYPE = get_mission_type(MISSION_ARG)
        match MISSION_TYPE:
            case MissionType.MISSION1:
                logger.info(
                    f"Using Mission Data {MissionType.MISSION1.value}")
            case _:
                logger.error("Invalid mission type")
                raise ValueError("Invalid mission type")
            
    SERVICE_NAME = "replay system"
    try:
        REPLAY_COMMAND = [
            "python3", "-u", os.path.join("backend",
                                          "replay_system", "replay_engine.py"),
            "--device-rocket", DEVICE,
            "--mission-type", MISSION_TYPE.value,
        ]

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

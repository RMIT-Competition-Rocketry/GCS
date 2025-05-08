import logging
import cli.proccess as process
import os

def start_replay_system(logger: logging.Logger, DEVICE: str):
    SERVICE_NAME = "replay system"
    try:
        REPLAY_COMMAND = [
            "python3", "-u", os.path.join("backend",
                                          "replay_system", "replay_engine.py"),
            "--device-rocket", DEVICE
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
            name = SERVICE_NAME,
            parse_output=True,
            env = env,
        )
        emulator_process.start()
        
    except Exception as e:
        logger.error(
            f"An error occured while starting {SERVICE_NAME}: {e}"
        )
        return None, None
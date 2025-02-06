#!/usr/bin/env python3

import click
import cli.rocket_logging as rocket_logging
import logging
import cli.proccess as process
import subprocess
import sys
import time
import signal

logger: str = None
cleanup_reason: str = "Program completed or undefined exit"  # Default clenaup message
# # Event flag to avoid busy waiting after CLI work is done
# shutdown_event: bool = False


@click.group()
def cli():
    """CLI interface to manage GCS software initialisation"""
    pass


@click.command()
def run():
    """Start software for production usage in native environment. Indented for usage on GCS only"""
    logger.error("Production mode attempted. Not supported")
    raise NotImplementedError("Production setup not currently supported")


def start_fake_serial_device():
    """
    Starts a fake serial device using socat and logs the output.
    Returns a tuple containing the paths of the two generated pseudo-terminals.
    """
    try:

        SOCAT_COMMAND = ["socat", "-d", "-d",
                         "pty,raw,echo=0", "pty,raw,echo=0"]
        logger.debug(f"Starting socat with: {SOCAT_COMMAND}")
        socat_proccess = process.ERRLoggedSubProcess(
            SOCAT_COMMAND, name="socat")
        socat_proccess.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting a Socat fake serial device: {e}")
        return None, None


def start_fake_serial_device_emulator():
    try:

        # os.path.join("backend", "tools", "device_emulator.py")
        EMULATOR_COMMAND = [
            "python3", "-u", "-Xfrozen_modules=off", "-m", "backend.tools.device_emulator"
        ]

        logger.debug(f"Starting emulator module with: {EMULATOR_COMMAND}")

        # Add project root to PYTHONPATH for the subprocess
        # project_root = os.getcwd()
        # env = os.environ.copy()
        # env["PYTHONPATH"] = f"{project_root}{os.pathsep}{env.get('PYTHONPATH', '')}"

        emulator_process = process.LoggedSubProcess(
            EMULATOR_COMMAND,
            name="emulator",
            # env=env
        )
        emulator_process.start()

    except Exception as e:
        logger.error(
            f"An error occurred while starting the rocket AV emulator: {e}")
        return None, None


@click.command()
@click.option('--nodocker', is_flag=True, help="Run without Docker. This skips containerisation")
def dev(nodocker):
    """Start software in development mode"""
    def start_docker_container():
        try:
            logger.info("Building dev container")
            subprocess.run(["docker", "build", "-t", "rocket-dev",
                           "-f", "docker/Dockerfile.dev", "."], check=True)
            logger.info("Running dev container")
            subprocess.run(["docker", "run", "--rm", "-it",
                           "rocket-dev"], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Docker container: {e}")
            DOCKER_WARNING_TEXT = "PLEASE ENSURE DOCKER ENGINE IS RUNNING"
            logger.error(f"{'-'*len(DOCKER_WARNING_TEXT)}")
            logger.error(DOCKER_WARNING_TEXT)
            logger.error(f"{'-'*len(DOCKER_WARNING_TEXT)}")
            raise

    if nodocker:
        # This is called in Docker anyway.
        # Just to avoid recursive containerisation
        logger.info(
            "Starting development mode, skipping containerisation. This is OK if you are already in a Docker container")

    else:
        logger.info("Starting dev container in Docker")
        start_docker_container()

    # TODO: Check this, use device name from config. Extract logs on debug level.

    start_fake_serial_device()
    start_fake_serial_device_emulator()


def signal_handler(signum, frame):
    """Handle system signals and set an appropriate cleanup reason"""
    global cleanup_reason
    signal_map = {
        signal.SIGINT: "Keyboard Interrupt (SIGINT)",
        signal.SIGTERM: "Termination Request (SIGTERM)",
        signal.SIGHUP: "Terminal Hangup (SIGHUP)",
        signal.SIGQUIT: "Quit Signal (SIGQUIT)",
    }
    if signum in signal_map:
        cleanup_reason = signal_map[signum]
    else:
        cleanup_reason = f"Recieved unhandled signal: {signum}"
    cleanup()
    # This can be a graceful exit for now.
    # Might need to change for CI tests in future
    sys.exit(0)


def cleanup():
    """Run cleanup tasks before the program exits"""
    logger.warning(f"Running cleanup tasks - Reason: {cleanup_reason}")
    process.LoggedSubProcess.cleanup()


def main():
    global logger, cleanup_reason

    # Use groups for nested positional arugments `rocket run dev/prod`
    cli.add_command(run)
    cli.add_command(dev)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle process termination
    signal.signal(signal.SIGHUP, signal_handler)   # Handle terminal close
    # Handle quit signal (Ctrl+\)
    signal.signal(signal.SIGQUIT, signal_handler)

    rocket_logging.initialise()
    logger = logging.getLogger('rocket')

    try:
        # Tell click CLI to let me handle exceptions and stuff.
        # This is because we're in charge of subprocess and threads
        cli.main(args=sys.argv[1:], standalone_mode=False)

        # After CLI setup is done, start waiting (not busy waiting please)
        while True:
            # Keep program alive, but it doesn't need to do anything
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup_reason = "Keyboard Interrupt (Ctrl+C)"
        cleanup()
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        cleanup_reason = f"Unhandled Exception: {e}"
        cleanup()
        # I hope this doesn't mess with CI test results
        raise  # Re-raise the exception after cleanup


if __name__ == '__main__':
    main()

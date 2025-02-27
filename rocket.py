#!/usr/bin/env python3

import click
import cli.rocket_logging as rocket_logging
import logging
import cli.proccess as process
import subprocess
import sys
import time
import os
import signal
from cli.start_socat import start_fake_serial_device
from cli.start_emulator import start_fake_serial_device_emulator
from cli.start_middleware_build import start_middleware_build, CMakeBuildModes
from cli.start_middleware import start_middleware, InterfaceType
from cli.start_event_viewer import start_event_viewer


logger: logging.Logger = None
cleanup_reason: str = "Program completed or undefined exit"  # Default clenaup message


@click.group()
def cli():
    """CLI interface to manage GCS software initialisation"""
    pass


@click.command()
def run():
    """Start software for production usage in native environment. Indented for usage on GCS only"""

    print_splash()
    logger.setLevel(logging.INFO)

    # 1. Make sure C++ middleware is there
    # TODO add checks for ALL files please
    # TODO please add a check to make sure it's up to date?
    if not (os.path.exists(os.path.join("build", "middleware-release"))):
        logger.error(
            "C++ release middleware not found. Please build it with release.sh. Exiting")
        raise FileNotFoundError("C++ release middleware not found. Exiting")

    # cheeky temp debug everywhere below
    # cheeky temp debug everywhere below
    # cheeky temp debug everywhere below
    # cheeky temp debug everywhere below
    devices = start_fake_serial_device(logger)
    if devices == (None, None):
        raise RuntimeError("Failed to start fake serial device. Exiting")

    # 2. Run C++ middleware
    # Note that devices are paired pseudo-ttys
    try:
        start_middleware(logger=logger,
                         release=True,
                         INTERFACE_TYPE=InterfaceType.TEST,
                         DEVICE_PATH=devices[0],
                         SOCKET_PATH="gcs_rocket")
    except Exception as e:
        logger.error(
            f"Failed to start middleware: {e}\nPropogating fatal error")
        raise

    time.sleep(0.5)

    # 4. Start device emulator
    # TODO maybe consider blocking further starts if this fails?
    # Would only be for convienece though. It isn't really required or critical
    start_fake_serial_device_emulator(logger, devices[1])

    # 5. Start the event viewer
    start_event_viewer(logger, "gcs_rocket", file_logging_enabled=True)

    # 6. Could start the pendent emulator

    # 7. Database stuff in future


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

    print_splash()

    if nodocker:
        # This is called in Docker anyway.
        # Just to avoid recursive containerisation
        logger.info(
            "Starting development mode, skipping containerisation. This is OK if you are already in a Docker container")

    else:
        logger.info("Starting dev container in Docker")
        start_docker_container()

    # 1. Build C++ middleware
    try:
        start_middleware_build(logger, CMakeBuildModes.DEBUG)
    except Exception as e:
        logger.error(
            f"Failed to build middleware: {e}\nPropogating fatal error")
        raise

    # 2.
    INTERFACE_TYPE = InterfaceType.UART
    match INTERFACE_TYPE:
        case InterfaceType.UART:
            logger.info("Starting UART interface")
            devices = ("/dev/serial0", None) # Just leave second (emulator) device as None
        case InterfaceType.TEST:
            logger.info("Starting TEST interface")
            devices = start_fake_serial_device(logger)
            if devices == (None, None):
                raise RuntimeError("Failed to start fake serial device. Exiting")
        case _:
            logger.error("Invalid interface type")
            raise ValueError("Invalid interface type")

    # 3. Run C++ middleware
    # Note that devices are paired pseudo-ttys
    try:
        start_middleware(logger=logger,
                         release=False,
                         INTERFACE_TYPE=INTERFACE_TYPE,
                         DEVICE_PATH=devices[0],
                         SOCKET_PATH="gcs_rocket")
    except Exception as e:
        logger.error(
            f"Failed to start middleware: {e}\nPropogating fatal error")
        raise

    # TODO fix this with middleware blocking
    time.sleep(0.5)

    # 4. Start device emulator
    # TODO maybe consider blocking further starts if this fails?
    # Would only be for convienece though. It isn't really required or critical
    if INTERFACE_TYPE == InterfaceType.TEST:
        start_fake_serial_device_emulator(logger, devices[1])

    # 5. Start the event viewer
    start_event_viewer(logger, "gcs_rocket", file_logging_enabled=False)

    # 6. Could start the pendent emulator

    # 7. Database stuff in future


def print_splash():
    """Prints a logo and splash screen for decoration"""
    with open(os.path.join("cli", "ascii_art_logo.txt"), "r") as r:
        print(r.read())

    print("\n\n")
    print("RMIT High Velocty Rocket GCS CLI")
    print("Version: ", end='')
    with open("VERSION", "r") as r:
        print(r.read())

    print("Local Timestamp: ", time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()))

    print("\n")


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
    if "Keyboard Interrupt" in cleanup_reason:
        print()  # Print a newline after the ^C
    logger.warning(f"Running cleanup tasks - Reason: {cleanup_reason}")
    process.LoggedSubProcess.cleanup()
    logger.info("All cleanup tasks completed")


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
        # I have a feeling this will never execute with the signal handlers?
        cleanup_reason = "Keyboard Interrupt (Ctrl+C)"
        print()  # Print a newline after the ^C
        cleanup()
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        cleanup_reason = f"Unhandled Exception: {e}"
        cleanup()
        # I hope this doesn't mess with CI test results
        raise  # Re-raise the exception after cleanup


if __name__ == '__main__':
    main()

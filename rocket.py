#!/usr/bin/env python3

import click
import cli.rocket_logging as rocket_logging
import cli.proccess as process
import config.config as config
import logging
import subprocess
import sys
import time
import os
import signal
import enum
from typing import Optional
from cli.start_socat import start_fake_serial_device
from cli.start_emulator import start_fake_serial_device_emulator
from cli.start_middleware_build import start_middleware_build, CMakeBuildModes
from cli.start_middleware import start_middleware, InterfaceType
from cli.start_event_viewer import start_event_viewer
from cli.start_pendant_emulator import start_pendant_emulator
from cli.start_frontend_api import start_frontend_api
from cli.start_simulation import start_simulator


logger: logging.Logger = None
cleanup_reason: str = "Program completed or undefined exit"  # Default clenaup message


def get_interface_type(interface: Optional[str]) -> InterfaceType:
    """Get the interface type from the command line argument or config"""
    if interface is None:  # Unspecified by user
        interface = config.load_config(
        )['hardware']['interface'].strip().upper()
        logger.debug(f"Using interface type from config: {interface}")
    else:
        interface = interface.strip().upper()
        logger.debug(f"Using interface type from CLI: {interface}")

    # Convert string to InterfaceType enum
    try:
        for enum_member in InterfaceType:
            if enum_member.name == interface:
                return enum_member
        # If we get here, no matching enum value was found
        valid_types = [e.name for e in InterfaceType]
        raise ValueError(
            f"Invalid interface type: '{interface}'. Valid types are: {', '.join(valid_types)}")
    except Exception as e:
        logger.error(f"Error processing interface type: {e}")
        raise ValueError(f"Invalid interface type: {interface}")


def shared_dev_options(func):
    """Decorator to add all dev command options to simulation."""
    # Reuse dev's options
    func = click.option('--docker', is_flag=True, help="Run in Docker")(func)
    func = click.option('--interface', type=click.Choice(
        [e.value for e in InterfaceType], case_sensitive=False),
        help="Hardware interface type. Overrides config parameter")(func)
    func = click.option('--nobuild', is_flag=True,
                        help="Do not build binaries. Search for pre-built binaries")(func)
    func = click.option('--logpkt', is_flag=True,
                        help="Log packet data to csv")(func)
    func = click.option('--nopendant', is_flag=True,
                        help="Do not run the pendant emulator")(func)
    return func


def start_docker_container(logger):
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


class Command(enum.Enum):
    """Command enums to help start services"""
    RUN = enum.auto()
    DEV = enum.auto()
    SIMULATION = enum.auto()


def start_services(COMMAND: Command,
                   DOCKER: bool = False,
                   INTERFACE_ARG: Optional[InterfaceType] = None,
                   nobuild: bool = False,
                   logpkt: bool = False,
                   nopendant: bool = False):
    """Starts all services required for the given command.

    Args:
        COMMAND (Command): What mode are you running in?
    """
    print_splash()

    # 0. Start docker container if requested in dev environment
    if not DOCKER:
        # This is called in Docker anyway.
        # Just to avoid recursive containerisation
        logger.info("Starting development mode")
    else:
        logger.info("Starting development container in Docker")
        start_docker_container(logger)

    # 0.1 Build C++ middleware
    if not nobuild and COMMAND == Command.DEV:
        try:
            start_middleware_build(logger, CMakeBuildModes.DEBUG)
        except Exception as e:
            logger.error(
                f"Failed to build middleware: {e}\nPropogating fatal error")
            raise
    else:
        logger.info("Skipping middleware build. Using pre-built binaries")

    # 2. Intialise devices and parameters
    INTERFACE_TYPE = get_interface_type(INTERFACE_ARG)
    match INTERFACE_TYPE:
        case InterfaceType.UART:
            logger.info("Starting UART interface")
            # Just leave second (emulator) device as None
            devices = ("/dev/ttyAMA0", None)
        case InterfaceType.TEST:
            if COMMAND == Command.RUN:
                logger.warning("Test interface selected in production mode")
            logger.info("Starting TEST interface")
            devices = start_fake_serial_device(logger)
            if devices == (None, None):
                raise RuntimeError(
                    "Failed to start fake serial device. Exiting")
        case _:
            logger.error("Invalid interface type")
            raise ValueError("Invalid interface type")

    # 3. Run C++ middleware
    # Note that `devices` are paired pseudo-ttys
    try:
        start_middleware(logger=logger,
                         release=COMMAND == Command.RUN,
                         INTERFACE_TYPE=INTERFACE_TYPE,
                         DEVICE_PATH=devices[0],
                         SOCKET_PATH="gcs_rocket")
    except Exception as e:
        logger.error(
            f"Failed to start middleware: {e}\nPropogating fatal error")
        raise

    # TODO fix this with middleware callback blocking
    # Sleep to make sure server and interface have started before starting emulator
    time.sleep(0.5)

    # 4. Start device emulator
    # TODO maybe consider blocking further starts if this fails?
    # Would only be for convienece though. It isn't really required or critical
    if INTERFACE_TYPE == InterfaceType.TEST and COMMAND == Command.DEV:
        start_fake_serial_device_emulator(logger, devices[1])
    elif COMMAND == Command.SIMULATION:
        start_simulator(logger, devices[1])

    # 5. Start the event viewer
    start_event_viewer(logger, "gcs_rocket", file_logging_enabled=logpkt)

    # 6. Start the pendent emulator
    if not nopendant:
        start_pendant_emulator(logger)

    # 7. Start the webcocket / frontend API
    start_frontend_api(logger, "gcs_rocket")


@click.group()
def cli():
    """CLI interface to manage GCS software initialisation"""
    # Check you're in a valid directory.
    # Implicit check is to make sure the logo file exists in expected spot
    if not os.path.exists(os.path.join("cli", "ascii_art_logo.txt")):
        raise RuntimeError(
            "Please run this program from project root directory")


@click.command()
def run():
    """Start software for launch day usage"""
    # Set logging level to INFO for production here. Issue: #93
    # ...
    start_services(Command.RUN,
                   DOCKER=False,
                   INTERFACE_ARG=None,  # Should use config only. Arg is not available for run mode
                   nobuild=True,  # Do NOT auto build in production mode.
                   logpkt=True,  # Log packets by default in production mode
                   nopendant=False  # Pendant emulator is required in production mode
                   )


@click.command()
@shared_dev_options
def dev(docker, interface, nobuild, logpkt, nopendant):
    """Start software in development mode"""
    start_services(Command.DEV,
                   DOCKER=docker,
                   INTERFACE_ARG=interface,
                   nobuild=nobuild,
                   logpkt=logpkt,
                   nopendant=nopendant
                   )


@click.command()
@shared_dev_options
def simulation(docker, interface, nobuild, logpkt, nopendant):
    """Start software in simulation mode"""
    start_services(Command.SIMULATION,
                   DOCKER=docker,
                   INTERFACE_ARG=interface,
                   nobuild=nobuild,
                   logpkt=logpkt,
                   nopendant=nopendant
                   )


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
    cli.add_command(simulation)

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

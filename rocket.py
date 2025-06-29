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
from typing import Optional, Callable
from cli.start_socat import start_fake_serial_device
from cli.start_emulator import start_fake_serial_device_emulator
from cli.start_middleware_build import start_middleware_build, CMakeBuildModes
from cli.start_middleware import start_middleware, InterfaceType, get_interface_type
from cli.start_event_viewer import start_event_viewer
from cli.start_pendant_emulator import start_pendant_emulator
from cli.start_frontend_api import start_frontend_api
from cli.start_simulation import start_simulator
from cli.start_frontend_webserver import start_frontend_webserver
from cli.start_replay_system import start_replay_system, get_available_missions, SimulationType
from cli.start_pendant_daemon import start_pendant_daemon


logger: logging.Logger = None
cleanup_reason: str = "Program completed or undefined exit"  # Default clenaup message
running_services: bool = False  # To help close the cli automatically


class Command(enum.Enum):
    """Command enums to help start services"""
    RUN = enum.auto()
    DEV = enum.auto()
    SIMULATION = enum.auto()
    REPLAY = enum.auto()


class DecoratorSelector(enum.Enum):
    """Selection options to build a decorator"""
    ALL_DEV = enum.auto()  # Give me all the dev options
    SIM = enum.auto()  # Give me the options for simulation
    GSE_ONLY = enum.auto()  # Give me just the GSE only option
    REPLAY = enum.auto()


class ControllerTypes(enum.Enum):
    """Nomenclature: this is also called a pendant"""
    F710 = enum.auto()
    RPI_GPIO_DEVICE = enum.auto()


def cli_decorator_factory(SELECTOR: DecoratorSelector):
    """Factory function to create decorators based on the selector"""
    def _set_level(ctx, param, value):
        if value:
            CLEAN_VALUE = value.upper().strip()
            rocket_logging.set_console_log_level(CLEAN_VALUE)
        return value

    _LOG_LEVEL_CHOICES = click.Choice(list(rocket_logging.LOG_MAPPING.keys()),
                                      case_sensitive=False)
    _INTERFACE_CHOICES = click.Choice(
        [e.value for e in InterfaceType], case_sensitive=False)
    _MISSION_CHOICES = click.Choice(
        get_available_missions(), case_sensitive=False)

    _REPLAY_MODES = click.Choice(
        ['mission', 'simulation'], case_sensitive=False
    )

    _SIMULATION_CHOICES = click.Choice(
        [e.value for e in SimulationType], case_sensitive=False
    )

    OPTIONS_GSE_ONLY = [click.option('--gse-only', is_flag=True,
                                     help="Run the system in GSE only mode")]

    OPTIONS_SIM = [
        click.option('-l', '--log-level', is_flag=False, type=_LOG_LEVEL_CHOICES,
                     help="Overide the config log level",
                     callback=_set_level, expose_value=False),
        click.option('--docker', is_flag=True,
                     help="Run in Docker"),
        click.option('--nobuild', is_flag=True,
                     help="Do not build binaries. Search for pre-built binaries"),
        click.option('--logpkt', is_flag=True,
                     help="Log packet data to csv")
    ]

    OPTIONS_REPLAY = [
        click.option('-l', '--log-level', is_flag=False, type=_LOG_LEVEL_CHOICES,
                     help="Overide the config log level",
                     callback=_set_level, expose_value=False),
        click.option('--docker', is_flag=True,
                     help="Run in Docker"),
        click.option('--nobuild', is_flag=True,
                     help="Do not build binaries. Search for pre-built binaries"),
        click.option('--logpkt', is_flag=True,
                     help="Log packet data to csv"),
        click.option('--mode', type=_REPLAY_MODES,
                     help="Select the replay mode"),
        click.option('--mission', type=_MISSION_CHOICES,
                     help="Select what mission to replay (required for mission mode)"),
        click.option('-s', '--simulation', type=_SIMULATION_CHOICES,
                     help="Select simulation type (required for simulation mode)")
    ]

    OPTIONS_ALL_DEV = OPTIONS_SIM + OPTIONS_GSE_ONLY + [
        click.option('-i', '--interface', type=_INTERFACE_CHOICES,
                     help="Hardware interface type. Overrides config parameter"),
        click.option('--nopendant', is_flag=True,
                     help="Do not run the pendant emulator"),
        click.option('--frontend', is_flag=True,
                     help="Run GSC front end server"),
        click.option('--experimental', is_flag=True,
                     help="Simulate ALL values over all possible domains"),
        click.option('--corruption', is_flag=True,
                     help="Simulate heavy bit corruption"),
    ]

    if SELECTOR == DecoratorSelector.ALL_DEV:
        OPTIONS = OPTIONS_ALL_DEV
    elif SELECTOR == DecoratorSelector.SIM:
        OPTIONS = OPTIONS_SIM
    elif SELECTOR == DecoratorSelector.GSE_ONLY:
        OPTIONS = OPTIONS_GSE_ONLY
    elif SELECTOR == DecoratorSelector.REPLAY:
        OPTIONS = OPTIONS_REPLAY

    def decorator(func: Callable) -> Callable:
        # Apply in reverse so the first in the list appears first in --help
        for option in reversed(OPTIONS):
            func = option(func)
        return func

    return decorator


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


def get_controller_enum() -> ControllerTypes:
    pedant_config = config.load_config()["hardware"].get("controller")
    if pedant_config is None or len(pedant_config) == 0:
        # Nothing specified
        raise RuntimeError("Pendant controller option not found in config.ini")
    match pedant_config.lower().strip():
        case "f710":
            return ControllerTypes.F710
        case "rpi_gpio_device":
            return ControllerTypes.RPI_GPIO_DEVICE
        case _:
            raise RuntimeError(
                "Pendant controller option not found in config.ini")


def start_services(COMMAND: Command,
                   DOCKER: bool = False,
                   INTERFACE_ARG: Optional[InterfaceType] = None,
                   nobuild: bool = False,
                   logpkt: bool = False,
                   nopendant: bool = False,
                   gse_only: bool = False,
                   frontend: bool = False,
                   replay_mode: Optional[str] = None,
                   MISSION_ARG: Optional[str] = None,
                   SIMULATION_ARG: Optional[str] = None,
                   experimental: bool = False,
                   corruption: bool = False):
    """Starts all services required for the given command.

    Args:
        COMMAND (Command): Summoning command for context.
        DOCKER (bool, optional): Start in docker?. Defaults to False.
        INTERFACE_ARG (Optional[InterfaceType], optional): Hardware interface to use. Defaults to None.
        nobuild (bool, optional): Skip cmake build?. Defaults to False.
        logpkt (bool, optional): Log recieved packets?. Defaults to False.
        nopendant (bool, optional): Don't start GSE control pendant?. Defaults to False.
        gse_only (bool, optional): Only communicate with GSE?. Defaults to False.
        frontend (bool, optional): Start the frontend server?. Defaults to False.
        replay_mode (Optional[str], optional): _description_. Defaults to None.
        MISSION_ARG (Optional[str], optional): _description_. Defaults to None.
        SIMULATION_ARG (Optional[str], optional): _description_. Defaults to None.
        experimental (bool, optional): Simulate all possible values over the entire domain. Defaults to False.
        corruption (bool, optional): Corrupt data packets to simulate heavy bit corruption. Defaults to False.

    Raises:
        NotImplementedError: _description_
        ValueError: _description_
    """
    global running_services
    running_services = True

    print_splash()

    # 0. Start docker container if requested in dev environment
    if not DOCKER:
        # This is called in Docker anyway.
        # Just to avoid recursive containerisation
        logger.info("Starting development mode")
    else:
        logger.info("Starting development container in Docker")
        raise NotImplementedError(
            "Internal Docker implimentation is out of date. Do not use")
        start_docker_container(logger)

    # 1 Build C++ middleware
    if not nobuild:
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
            devices = ("/dev/serial0", None)
        case InterfaceType.TEST_UART:
            devices = run_pseudoterm_setup(COMMAND)
        case InterfaceType.TEST:
            devices = run_pseudoterm_setup(COMMAND)
        case _:
            logger.error("Invalid interface type")
            raise ValueError("Invalid interface type")

    # 3. Run C++ middleware
    # Note that `devices` are paired pseudo-ttys
    try:
        optional_arg = None
        if gse_only:
            optional_arg = "--GSE_ONLY"
        start_middleware(logger=logger,
                         release=COMMAND == Command.RUN,
                         INTERFACE_TYPE=INTERFACE_TYPE,
                         DEVICE_PATH=devices[0],
                         PENDANT_SOCKET_PATH="gcs_rocket",
                         WEB_CONTROL_SOCKET_PATH=os.path.abspath(os.path.join(
                             os.path.sep, 'tmp', 'gcs_rocket_web_pull.sock')
                         ),
                         opt_arg=optional_arg)
    except Exception as e:
        logger.error(
            f"Failed to start middleware: {e}\nPropogating fatal error")
        raise

    # 4. Start device emulator
    # TODO maybe consider blocking further starts if this fails?
    # Would only be for convienece though. It isn't really required or critical
    if INTERFACE_TYPE in [InterfaceType.TEST, InterfaceType.TEST_UART] \
            and COMMAND == Command.DEV:
        start_fake_serial_device_emulator(logger, devices[1],
                                          INTERFACE_TYPE,
                                          experimental=experimental,
                                          corruption=corruption)
    elif COMMAND == Command.SIMULATION:
        start_simulator(logger, devices[1])
    elif COMMAND == Command.REPLAY:
        if replay_mode == "mission":
            start_replay_system(
                logger, devices[1], MISSION=MISSION_ARG, SIMULATION=None)
        else:
            start_replay_system(
                logger, devices[1], MISSION=None, SIMULATION=SIMULATION_ARG)

    # 5. Start the event viewer
    start_event_viewer(logger, "gcs_rocket", file_logging_enabled=logpkt)

    # 6. Start the pendent emulator
    if not nopendant:
        controller_enum = get_controller_enum()
        if controller_enum == ControllerTypes.F710:
            start_pendant_emulator(logger)
        elif controller_enum == ControllerTypes.RPI_GPIO_DEVICE:
            start_pendant_daemon(logger)
        else:
            raise NotImplementedError("Controller service not supported")

    if frontend:
        # 7. Start the websocket / frontend API
        start_frontend_api(logger, "gcs_rocket")
        # 8. Start the frontend web server
        start_frontend_webserver(logger)


def run_pseudoterm_setup(COMMAND: Command):
    if COMMAND == Command.RUN:
        logger.warning("Test interface selected in production mode")
    logger.info("Starting pseudo-terminals for emulation")
    devices = start_fake_serial_device(logger)
    if devices == (None, None):
        raise RuntimeError(
            "Failed to start fake serial device. Exiting")

    return devices


@click.group()
def cli():
    """CLI interface to manage GCS software initialisation"""
    # Check you're in a valid directory.
    # Implicit check is to make sure the logo file exists in expected spot
    if not os.path.exists(os.path.join("cli", "ascii_art_logo.txt")):
        raise RuntimeError(
            "Please run this program from project root directory")


@click.command()
@cli_decorator_factory(DecoratorSelector.GSE_ONLY)
def run(gse_only):
    """Start software for launch day usage"""
    rocket_logging.set_console_log_level("INFO")
    start_services(Command.RUN,
                   DOCKER=False,
                   INTERFACE_ARG=None,  # Should use config only. Arg is not available for run mode
                   nobuild=True,  # Do NOT auto build in production mode.
                   logpkt=True,  # Log packets by default in production mode
                   nopendant=False,  # Pendant emulator is required in production mode
                   gse_only=gse_only,
                   frontend=True  # Run frontend web server in production mode
                   )


@click.command()
@cli_decorator_factory(DecoratorSelector.ALL_DEV)
def dev(docker, interface, nobuild, logpkt, nopendant, gse_only, frontend, experimental, corruption):
    """Start software in development mode"""
    start_services(Command.DEV,
                   DOCKER=docker,
                   INTERFACE_ARG=interface,
                   nobuild=nobuild,
                   logpkt=logpkt,
                   nopendant=nopendant,
                   gse_only=gse_only,
                   frontend=frontend,
                   experimental=experimental,
                   corruption=corruption,
                   )


@click.command()
@cli_decorator_factory(DecoratorSelector.SIM)
def simulation(docker, nobuild, logpkt):
    """Start software in simulation mode"""
    start_services(Command.SIMULATION,
                   DOCKER=docker,
                   INTERFACE_ARG="TEST",
                   nobuild=nobuild,
                   logpkt=logpkt,
                   nopendant=True,
                   gse_only=False,
                   frontend=True
                   )


@click.command()
@cli_decorator_factory(DecoratorSelector.REPLAY)
def replay(docker, nobuild, logpkt, mode, mission, simulation):
    """Start software in simulation mode"""
    if not mode:
        raise click.UsageError("--mode is required for the replay engine")

    if mode == 'mission':
        if not mission:
            raise click.UsageError(
                "--mission is required to run a specified mission")
        elif mission == 'TEST':
            raise NotImplementedError(
                f"{mission} has not been implemented yet")

        logger.info(f"Using mission data:{mission}")

    elif mode == 'simulation':
        if not simulation:
            raise click.UsageError(
                "--simulation is required to run a specified scenario")
        elif simulation != 'TEST' and simulation != 'DEMO':
            raise NotImplementedError(
                f"{simulation} has not been implemented yet")
        logger.info(f"Running simulation: {simulation}")
    start_services(Command.REPLAY,
                   DOCKER=docker,
                   INTERFACE_ARG="TEST",
                   nobuild=nobuild,
                   logpkt=logpkt,
                   nopendant=True,
                   gse_only=False,
                   frontend=True,
                   replay_mode=mode,
                   MISSION_ARG=mission,
                   SIMULATION_ARG=simulation
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
    cli.add_command(replay)

    # Register custom signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle process termination
    signal.signal(signal.SIGHUP, signal_handler)   # Handle terminal close
    # Handle quit signal (Ctrl+\)
    signal.signal(signal.SIGQUIT, signal_handler)

    # Remove stale tmp files
    GCS_CONFIG_HELPER_PATH = os.path.join(
        os.path.sep, "tmp", "GCS_CONFIG_LOCATION.txt")
    if os.path.exists(GCS_CONFIG_HELPER_PATH):
        os.remove(GCS_CONFIG_HELPER_PATH)

    rocket_logging.initialise()
    logger = logging.getLogger('rocket')

    try:
        # Tell click CLI to let me handle exceptions and stuff.
        # This is because we're in charge of subprocess and threads
        cli.main(args=sys.argv[1:], standalone_mode=False)

        # After CLI setup is done, start waiting (not busy waiting please)
        if running_services:
            while True:
                # Keep program alive, but it doesn't need to do anything
                time.sleep(1)

    except Exception as e:
        cleanup_reason = f"Unhandled Exception: {e}"
        cleanup()
        # I hope this doesn't mess with CI test results
        raise  # Re-raise the exception after cleanup


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import click
import rocket_logging
import logging
import cli.proccess as process
import subprocess
import os
import atexit

logger: str = None


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
            # lol, um
            "python3", "-um", "backend.tools.device_emulator"
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


def main():
    global logger
    # Use groups for nested positional arugments `rocket run dev/prod`
    cli.add_command(run)
    cli.add_command(dev)
    # Register the cleanup method to be called on program exit.
    # This should work for subclassess I think?
    atexit.register(process.LoggedSubProcess.cleanup)
    rocket_logging.initialise()
    logger = logging.getLogger('rocket')
    cli()


if __name__ == '__main__':
    main()

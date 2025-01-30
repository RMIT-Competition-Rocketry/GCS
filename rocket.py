#!/usr/bin/env python3

import re
import click
import abc
import rocket_logging
import logging
import subprocess
import os
from typing import List, Optional
import asyncio
import threading

logger: str = None

# TODO: Create an ABC for logged proccesses
# TODO: Do some reasearch and drawings on the best way to handle subproccesses.
#   Do you start threads or make asyncronous handlers for each object?
# TODO: Include methods for starting, logging, threading?


class LoggedSubProcess():
    """Object to manage subproccess called by this CLI with centralised logging
    """

    def __init__(self, command: List[str], name: Optional[str] = None):
        super().__init__()
        self.logger = logging.getLogger('rocket')
        self.command = command
        self.name = name or " ".join(command)
        self.process: Optional[asyncio.subprocess.Process] = None
        self.logger_adapter = logging.LoggerAdapter(
            self.logger,
            extra={"subprocess_name": self.name}
        )

    async def start(self):
        """Start the subprocess and monitor its output"""
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self.logger.info(
            f"Started subprocess: {self.name} (PID: {self.process.pid})")

        await asyncio.gather(
            self._monitor_stream(self.process.stdout, "STDOUT"),
            self._monitor_stream(self.process.stderr, "STDERR"),
        )

    async def stop(self):
        """Stop the subprocess"""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            await self.process.wait()
            self.logger.info(
                f"Stopped subprocess: {self.name} (PID: {self.process.pid})")

    async def _monitor_stream(self, stream: asyncio.StreamReader, stream_name: str):
        """Monitor a stream (stdout or stderr) and log its output"""
        while not stream.at_eof():
            line = await stream.readline()
            if line:
                self.logger.debug(
                    f"[{self.name} {stream_name}] {line.decode().strip()}")


class LoggedSubProcess():
    """Object to manage subproccess called by this CLI with centralised logging
    """

    def __init__(self, command: List[str], name: Optional[str] = None):
        super().__init__()
        self.logger = logging.getLogger('rocket')
        self.command = command
        self.name = name or " ".join(command)
        self.process: Optional[asyncio.subprocess.Process] = None
        self.logger_adapter = logging.LoggerAdapter(
            self.logger,
            extra={"subprocess_name": self.name}
        )

    async def start(self):
        """Start the subprocess and monitor its output"""
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self.logger_adapter.info(
            f"Started subprocess: {self.name} (PID: {self.process.pid})")

        await asyncio.gather(
            self._monitor_stream(self.process.stdout, "STDOUT"),
            self._monitor_stream(self.process.stderr, "STDERR"),
        )

    async def stop(self):
        """Stop the subprocess"""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            await self.process.wait()
            self.logger_adapter.info(
                f"Stopped subprocess: {self.name} (PID: {self.process.pid})")

    async def _monitor_stream(self, stream: asyncio.StreamReader, stream_name: str):
        """Monitor a stream (stdout or stderr) and log its output"""
        while not stream.at_eof():
            line = await stream.readline()
            if line:
                if stream_name == "STDERR":
                    self.logger_adapter.error(
                        f"[{stream_name}] {line.decode().strip()}")
                else:
                    self.logger_adapter.debug(
                        f"[{stream_name}] {line.decode().strip()}")


class ERRLoggedSubProcess(LoggedSubProcess):
    """Subclass of LoggedSubProcess that logs STDERR as debug instead of error.
    This is used for Socat, which has to output all of its stuff to STDERR
    """

    async def _monitor_stream(self, stream: asyncio.StreamReader, stream_name: str):
        """Monitor a stream (stdout or stderr) and log its output"""
        while not stream.at_eof():
            line = await stream.readline()
            if line:
                self.logger_adapter.debug(
                    f"[{stream_name}] {line.decode().strip()}")


@click.group()
def cli():
    """CLI interface to manage GCS software initialisation"""
    pass


@click.command()
def run():
    """Start software for production usage in native environment. Indented for usage on GCS only"""
    logger.error("Production mode attempted. Not supported")
    raise NotImplementedError("Production setup not currently supported")


async def start_fake_serial_device():
    """
    Starts a fake serial device using socat and logs the output.
    Returns a tuple containing the paths of the two generated pseudo-terminals.
    """
    try:

        SOCAT_COMMAND = ["socat", "-d", "-d",
                         "pty,raw,echo=0", "pty,raw,echo=0"]
        logger.debug(f"Starting socat with: {SOCAT_COMMAND}")
        socat_proccess = ERRLoggedSubProcess(SOCAT_COMMAND, name="socat")
        tasks = []
        tasks.append(asyncio.create_task(socat_proccess.start()))

        # how does await work here. Does it implicitly call the start method and wait until code reaches the await line??
        await asyncio.gather(*tasks)

    except Exception as e:
        logger.error(
            f"An error occurred while starting a Socat fake serial device: {e}")
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

    asyncio.run(start_fake_serial_device())

    # This has relative import errors
    # subprocess.run(["python3", os.path.join(
    #     "backend", "tools", "device_emulator.py")], check=True)


# Use groups for nested positional arugments `rocket run dev/prod`
cli.add_command(run)
cli.add_command(dev)

if __name__ == '__main__':
    rocket_logging.initialise()
    logger = logging.getLogger('rocket')
    cli()

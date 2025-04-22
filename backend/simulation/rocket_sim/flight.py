from rocket_sim.rocket import create_rocket
from rocket_sim.environment import create_environment
from rocket_sim.config import get_flight_config
from rocketpy import Flight
import backend.includes_python.process_logging as slogger
import backend.includes_python.service_helper as service_helper


def run_flight():
    """
        Runs the flight simulation based on the rocket and environmental factors
        Please refer to config files for the rail length, inclination and heading
    """
    rocket = create_rocket()
    if service_helper.time_to_stop():
        return
    slogger.info("Rocket has been successfully created!")
    slogger.info("Creating environment...")
    env = create_environment()
    if service_helper.time_to_stop():
        return
    slogger.info("Environment has been successfully created!")
    slogger.info("Creating flight config...")
    cfg = get_flight_config()
    if service_helper.time_to_stop():
        return
    slogger.info("Flight config has been successfully created!")
    return Flight(rocket=rocket, environment=env, rail_length=cfg["rail_length"], inclination=cfg["inclination"], heading=cfg["heading"])

from rocket_sim.rocket import create_rocket
from rocket_sim.environment import create_environment
from rocket_sim.config import get_flight_config
from rocketpy import Flight

def run_flight():
    """
        Runs the flight simulation based on the rocket and environmental factors
        Please refer to config files for the rail length, inclination and heading
    """
    rocket = create_rocket()
    env = create_environment()
    cfg = get_flight_config
    return Flight(rocket=rocket, environment=env, rail_length=cfg["rail_length"], inclination=cfg["inclination"], heading=cfg["heading"])
from rocket_sim.rocket import create_rocket
from rocket_sim.environment import create_environment
from rocketpy import Flight

def run_flight():
    rocket = create_rocket()
    env = create_environment()
    return Flight(rocket=rocket, environment=env, rail_length=5.2, inclination=85, heading=0)
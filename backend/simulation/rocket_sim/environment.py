import datetime
from rocketpy import Environment
from backend.simulation.rocket_sim.config import get_env_config


def create_environment():
    """
        This file is needed for the flight simulation
    """
    # Get the config
    cfg = get_env_config()
    # Create the environment object needed for the flight
    env = Environment(latitude=cfg["latitude"], longitude=-
                      cfg["longitude"], elevation=cfg["elevation"])
    # Required by rocketpy for "launch time"
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    env.set_date((tomorrow.year, tomorrow.month, tomorrow.day, 12))  # UTC time
    env.set_atmospheric_model(type=cfg["atmospheric_type"], file="GFS")
    env.max_expected_height = cfg["max_height"]  # Adjusts plot height

    return env

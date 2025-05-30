from backend.simulation.rocket_sim.flight import run_flight
import pandas as pd
import backend.includes_python.process_logging as slogger
import os
import shutil
from backend.simulation.rocket_sim.config import hash_ini_file
import json


def determine_flight_state(t: int, max_speed_time: int, apogee_time: int, landing_time: int) -> int:
    """Determine the flight state based on elapsed time."""
    # 0.1% tolerance for the apogee
    tolerance_amount = 0.00001
    if t <= 0:
        return 0  # Pre-launch or invalid time
    if t < max_speed_time:
        return 1  # Launch
    if t < apogee_time * (1 - tolerance_amount):
        return 2  # Coast
    if t < apogee_time * (1 + tolerance_amount):
        return 3  # Apogee
    if t < landing_time:
        return 4  # Descent
    return 5  # Landed


def get_simulated_flight_data() -> pd.DataFrame:
    """
        Use this function to run the api, you will get all the necessary data for the backend in a pandas dataframe
    """
    CONFIG_HASH = hash_ini_file()
    CACHE_DIRS = os.path.join("backend", "simulation", "cache")
    THIS_CACHE_DIR = os.path.join(CACHE_DIRS, CONFIG_HASH)
    csv_export_name = os.path.join(THIS_CACHE_DIR, "flightdataexport.csv")
    cache_building_lock_name = os.path.join(THIS_CACHE_DIR, "building.lock")
    extra_data_path = os.path.join(
        os.path.dirname(csv_export_name), "data.json")
    os.makedirs(CACHE_DIRS, exist_ok=True)

    build_data = True

    if CONFIG_HASH in os.listdir(CACHE_DIRS):
        if os.path.isfile(cache_building_lock_name):
            slogger.info("Cache was incomplete, removing it...")
            if os.path.exists(THIS_CACHE_DIR):
                shutil.rmtree(THIS_CACHE_DIR)
        else:
            slogger.info("Loading simulation flight data from cache...")
            build_data = False

    if build_data:
        # Make new data
        # Create missing files and directories
        os.makedirs(os.path.dirname(csv_export_name), exist_ok=True)
        # Add a lockfile to indicate that the cache is being built
        open(cache_building_lock_name, "w").close()
        open(csv_export_name, "w").close()
        flight_object = run_flight()
        # w means the angular velocity
        # a is acceleration
        flight_object.export_data(
            csv_export_name,
            "altitude", "speed",
            "w1", "w2", "w3",
            "ax", "ay", "az",
            'e0', 'e1', 'e2', 'e3',
            'latitude', "longitude"
        )
        with open(extra_data_path, "w") as f:
            json.dump({
                "apogee_time": flight_object.apogee_time,
                "max_speed_time": flight_object.max_speed_time}, f)
        os.remove(cache_building_lock_name)

    if not os.path.isfile(csv_export_name):
        slogger.error("Could not fine flight data")

    flight_df = pd.read_csv(csv_export_name)

    with open(extra_data_path, "r") as f:
        extra_data = json.load(f)
        apogee_time = extra_data["apogee_time"]
        max_speed_time = extra_data["max_speed_time"]

    slogger.info("Flight has launched successfully!")

    # Grab the landing time which is just the last result in the simulation
    landing_time = flight_df["# Time (s)"].iloc[-1]
    # Add the state the rocket is in based on timestamps from simulation
    flight_df["flight_state"] = flight_df["# Time (s)"].apply(lambda t: determine_flight_state(
        t, max_speed_time=max_speed_time, apogee_time=apogee_time, landing_time=landing_time))
    # @TODO add some verification and testing if apogee exists.
    # Verify if apogee exists
    apogee_data = flight_df[flight_df["flight_state"] == 4]
    if apogee_data.empty:
        slogger.critical("THERE IS NO APOGEE DATA")

    return flight_df


def run_sim():
    run_flight()

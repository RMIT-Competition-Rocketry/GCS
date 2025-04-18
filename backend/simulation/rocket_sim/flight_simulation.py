from rocket_sim.flight import run_flight
import pandas as pd
import backend.process_logging as slogger


def determine_flight_state(t: int, max_speed_time: int, apogee_time: int, landing_time: int) -> int:
    """Determine the flight state based on elapsed time."""
    # 0.1% tolerance for the apogee
    tolerance_amount = 0.00001
    if t <= 0:
        return 1  # Pre-launch or invalid time
    if t < max_speed_time:
        return 2  # Launch
    if t < apogee_time * (1 - tolerance_amount):
        return 3  # Coast
    if t < apogee_time * (1 + tolerance_amount):
        return 4  # Apogee
    if t < landing_time:
        return 5  # Descent
    return 6  # Landed


def get_simulated_flight_data() -> pd.DataFrame:
    """
        Use this function to run the api, you will get all the necessary data for the backend in a pandas dataframe
    """
    test_flight = run_flight()
    slogger.info("Flight has launched successfully!")
    # Extract key information from the test flight
    # Using the apogee time and max speed time to find the launch states
    apogee_time = test_flight.apogee_time
    max_speed_time = test_flight.max_speed_time
    # The Export file is here
    csv_export_name = "backend/simulation/cache/flightdataexport.csv"
    # Export the test flight data
    # w means the angular velocity
    # a is acceleration
    test_flight.export_data(
        csv_export_name,
        "altitude", "speed",
        "w1", "w2", "w3",
        "ax", "ay", "az"
    )
    # Convert the test data csv into a pandas dataframe
    flight_data = pd.read_csv(csv_export_name)
    # Grab the landing time which is just the last result in the simulation
    landing_time = flight_data["# Time (s)"].iloc[-1]
    # Add the state the rocket is in based on timestamps from simulation
    flight_data["flight_state"] = flight_data["# Time (s)"].apply(lambda t: determine_flight_state(
        t, max_speed_time=max_speed_time, apogee_time=apogee_time, landing_time=landing_time))
    # @TODO add some verification and testing if apogee exists.
    # Verify if apogee exists
    apogee_data = flight_data[flight_data["flight_state"] == 4]
    if apogee_data.empty:
        slogger.critical("THERE IS NO APOGEE DATA")

    return flight_data


def run_sim():
    run_flight()

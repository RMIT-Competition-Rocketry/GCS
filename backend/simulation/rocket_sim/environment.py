import datetime
from rocketpy import Environment

def create_environment():
    env = Environment(latitude=32.990254, longitude=-106.974998, elevation=1400)
    
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    env.set_date((tomorrow.year, tomorrow.month, tomorrow.day, 12))  # UTC time
    env.set_atmospheric_model(type="Forecast", file="GFS")
    env.max_expected_height = 5000  # Adjusts plot height

    return env
import configparser
"""
    CONFIG FOR EVERY MODULE IN ROCKET_SIM A PAIN IN THE ASS
"""
# Read the config
config = configparser.ConfigParser()
config.read("backend/simulation/simulation.ini")

def get_motor_config():
    """
        Grabs the motor config from the config ini used for rocket.py
    """
    motor = config["Motor"]
    return {
        "thrust_start": float(motor["thrust_start"]),
        "thrust_end": float(motor["thrust_end"]),
        "burn_time": float(motor["burn_time"]),
        "dry_mass": float(motor["dry_mass"]),
        "dry_inertia": (
            float(motor["dry_inertia_x"]),
            float(motor["dry_inertia_y"]),
            float(motor["dry_inertia_z"])
        ),
        # Need to convert to mm -> m
        "nozzle_radius": float(motor["nozzle_radius"]),
        "throat_radius": float(motor["throat_radius"]), 
        "grain_number": int(motor["grain_number"]),
        "grain_separation": float(motor["grain_separation"]),
        "grain_outer_radius": float(motor["grain_outer_radius"]),
        "grain_initial_inner_radius": float(motor["grain_initial_inner_radius"]),
        "grain_initial_height": float(motor["grain_initial_height"]),
        "grain_density": float(motor["grain_density"]),
        "grains_com": float(motor["grains_com_position"]),
        "dry_cm": float(motor["dry_cm_position"]),
        "nozzle_position": float(motor["nozzle_position"]),
        "tank_position": float(motor["tank_position"]),
    }
    
def get_rocket_config():
    """
    Gets the rocket config
    """
    rocket = config["Rocket"]
    return {
        # Converting from mm to m
        "radius": float(rocket["radius"]),
        "mass": float(rocket["mass"]),
        "inertia": (
            float(rocket["inertia_x"]),
            float(rocket["inertia_y"]),
            float(rocket["inertia_z"]),
        ),
        "com_without_motor": float(rocket["com_without_motor"]),
        "orientation": rocket["orientation"],
        "motor_position": float(rocket["motor_position"]),

    }
    
    
def get_flight_config():
    """
        Returns the rail length, inclination and heading in a dictionary
    """
    f = config["Flight"]
    return {
        "rail_length": float(f["rail_length"]),
        "inclination": float(f["inclination"]),
        "heading": float(f["heading"]),
    }
    
def get_env_config():
    """
        Returns the latitude, longitude, elevation and max height of the flight environment
    """
    e = config["Environment"]
    return {
        "latitude": float(e["latitude"]),
        "longitude": float(e["longitude"]),
        "elevation": float(e["elevation"]),
        "atmospheric_type": (e["atmospheric_type"]),
        "atmospheric_model_file": (e["atmospheric_model_file"]),
        "max_height": float(e["max_height"])
    }
    
def get_fuel_tank_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)

    # Fuel
    oxidizer_liq_name = config['Fuel']['oxidizer_liquid_name']
    oxidizer_liq_density = float(config['Fuel']['oxidizer_liquid_density'])
    oxidizer_gas_name = config['Fuel']['oxidizer_gas_name']
    oxidizer_gas_density = float(config['Fuel']['oxidizer_gas_density'])

    # Tank Geometry
    #tank_type = config['tank_geometry']['tank_type']
    radius = eval(config['tank_geometry']['radius'])
    height = float(config['tank_geometry']['height'])

    # Oxidizer Tank
    flux_time = float(config['oxidizer_tank']['flux_time'])
    initial_liquid_mass = float(config['oxidizer_tank']['initial_liquid_mass'])
    initial_gas_mass = float(config['oxidizer_tank']['initial_gas_mass'])
    liquid_mass_flow_rate_in = float(config['oxidizer_tank']['liquid_mass_flow_rate_in'])
    liquid_mass_flow_rate_out = eval(config['oxidizer_tank']['liquid_mass_flow_rate_out'])
    gas_mass_flow_rate_in = float(config['oxidizer_tank']['gas_mass_flow_rate_in'])
    gas_mass_flow_rate_out = float(config['oxidizer_tank']['gas_mass_flow_rate_out'])

    # Return the values (could use these to create objects)
    return {
        'fuels': {
            'liquid': {'name': oxidizer_liq_name, 'density': oxidizer_liq_density},
            'gas': {'name': oxidizer_gas_name, 'density': oxidizer_gas_density}
        },
        'tank': {
            #'type': tank_type,
            'geometry': {'radius': radius, 'height': height},
            'oxidizer_tank': {
                'flux_time': flux_time,
                'initial_liquid_mass': initial_liquid_mass,
                'initial_gas_mass': initial_gas_mass,
                'liquid_mass_flow_rate_in': liquid_mass_flow_rate_in,
                'liquid_mass_flow_rate_out': liquid_mass_flow_rate_out,
                'gas_mass_flow_rate_in': gas_mass_flow_rate_in,
                'gas_mass_flow_rate_out': gas_mass_flow_rate_out
            }
        }
    }
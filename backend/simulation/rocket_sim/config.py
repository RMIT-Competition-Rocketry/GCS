import configparser

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
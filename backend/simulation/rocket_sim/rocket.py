from rocketpy import HybridMotor, Rocket
from rocket_sim.fuel import create_oxidizer_tank
from rocket_sim.config import get_motor_config, get_rocket_config

def create_hybrid_motor():
    """
        Currently only implementation from a basic hybrid motor
    """
    config = get_motor_config()
    thrust_calculation = lambda t: config["thrust_start"] - (
        config["thrust_start"] - config["thrust_end"]) / config["burn_time"] * t
    hybrid_motor= HybridMotor(
        thrust_source=thrust_calculation,
        dry_mass=config["dry_mass"],
        dry_inertia=config["dry_inertia"],
        nozzle_radius=config["nozzle_radius"] / 2000,
        throat_radius=config["throat_radius"] /2000,
        grain_number=config["grain_number"],
        grain_separation=config["grain_separation"],
        grain_outer_radius=config["grain_outer_radius"],
        grain_initial_inner_radius=config["grain_initial_inner_radius"],
        grain_initial_height=config["grain_initial_height"],
        grain_density=config["grain_density"],
        grains_center_of_mass_position=config["grains_com"],
        center_of_dry_mass_position=config["dry_cm"],
        nozzle_position=config["nozzle_position"],
        burn_time=config["burn_time"]
        
    )

    oxidizer_tank = create_oxidizer_tank()
    hybrid_motor.add_tank(tank=oxidizer_tank, position=config["tank_position"])
    return hybrid_motor

def create_rocket():
    config = get_rocket_config()
    test_rocket = Rocket(
        radius=config["radius"] / 2000,
        mass=config["mass"],
        inertia=config["inertia"],
        power_off_drag="backend/simulation/sim_data/powerOffDragCurve.csv",
        power_on_drag="backend/simulation/sim_data/powerOffDragCurve.csv",
        center_of_mass_without_motor=config["com_without_motor"],
        coordinate_system_orientation=config["orientation"],
    )

    rail_buttons = test_rocket.set_rail_buttons(
        upper_button_position=0.0818,
        lower_button_position=-0.618,
        angular_position=45,
    )

    test_motor = create_hybrid_motor()
    test_rocket.add_motor(test_motor, position=config["motor_position"])

    # Aerodynamic surfaces
    test_rocket.add_nose(length=0.55829, kind="vonKarman", position=1.278)
    test_rocket.add_trapezoidal_fins(
        n=4, root_chord=0.120, tip_chord=0.060, span=0.110, position=-1.04956
    )
    test_rocket.add_tail(top_radius=0.0635, bottom_radius=0.0435, length=0.060, position=-1.194656)

    # Parachutes
    test_rocket.add_parachute(
        "Main",
        cd_s=10.0,
        trigger=800,
        sampling_rate=105,
        lag=1.5,
        noise=(0, 8.3, 0.5),
    )

    test_rocket.add_parachute(
        "Drogue",
        cd_s=1.0,
        trigger="apogee",
        sampling_rate=105,
        lag=1.5,
        noise=(0, 8.3, 0.5),
    )

    return test_rocket

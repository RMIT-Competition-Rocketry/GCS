from rocketpy import HybridMotor
from backend.simulation.rocket_sim.fuel import create_oxidizer_tank
from backend.simulation.rocket_sim.config import get_motor_config


def create_hybrid_motor():
    """
        Currently only implementation from a basic hybrid motor
    """
    config = get_motor_config()

    def thrust_calculation(t): return config["thrust_start"] - (
        config["thrust_start"] - config["thrust_end"]) / config["burn_time"] * t
    hybrid_motor = HybridMotor(
        thrust_source=thrust_calculation,
        dry_mass=config["dry_mass"],
        dry_inertia=config["dry_inertia"],
        nozzle_radius=config["nozzle_radius"] / 2000,
        throat_radius=config["throat_radius"] / 2000,
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

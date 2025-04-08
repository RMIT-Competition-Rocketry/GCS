from rocketpy import Rocket
from rocket_sim.engine import create_hybrid_motor
from rocket_sim.config import get_rocket_config



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

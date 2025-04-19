from rocketpy import Fluid, CylindricalTank, MassFlowRateBasedTank
from rocket_sim.config import get_fuel_tank_config

def create_oxidizer_tank():
    """
        Creates the tank necessary for hybrid motors
        Requires a fuel and the calculations for gas and liquid flow in and out
        Will also require the tank shape
    """
    # Creating fuel examples
    cfg = get_fuel_tank_config()
    oxidizer_liq = Fluid(name=cfg["fuels"]["liquid"]["name"], density=cfg["fuels"]["liquid"]["density"])
    oxidizer_gas = Fluid(name=cfg["fuels"]["gas"]["name"], density=cfg["fuels"]["liquid"]["density"])
    # Get tank geometry
    tank_shape = CylindricalTank(cfg["tank"]["geometry"]["radius"], cfg["tank"]["geometry"]["height"])

    # Define the tank
    # Since it is a massflow rate based tank this means that the mass flow rates of the liquid
    # and gas are defined by the user.
    oxidizer_tank = MassFlowRateBasedTank(
        name="oxidizer tank",
        geometry=tank_shape,
        flux_time=cfg["tank"]["oxidizer_tank"]["flux_time"],
        initial_liquid_mass=cfg["tank"]["oxidizer_tank"]["initial_liquid_mass"],
        initial_gas_mass=cfg["tank"]["oxidizer_tank"]["initial_gas_mass"],
        liquid_mass_flow_rate_in=cfg["tank"]["oxidizer_tank"]["liquid_mass_flow_rate_in"],
        liquid_mass_flow_rate_out=cfg["tank"]["oxidizer_tank"]["liquid_mass_flow_rate_out"],
        gas_mass_flow_rate_in=cfg["tank"]["oxidizer_tank"]["gas_mass_flow_rate_in"],
        gas_mass_flow_rate_out=cfg["tank"]["oxidizer_tank"]["gas_mass_flow_rate_out"],
        liquid=oxidizer_liq,
        gas=oxidizer_gas,
    )
    return oxidizer_tank
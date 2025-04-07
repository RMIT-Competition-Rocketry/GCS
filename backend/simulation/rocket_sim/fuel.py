from rocketpy import Fluid, CylindricalTank, MassFlowRateBasedTank
def create_oxidizer_tank():
    # Creating fuel examples
    oxidizer_liq = Fluid(name="N20_l", density=1220)
    oxidizer_gas = Fluid(name="N20_g", density=1.9277)

    # Get tank geometry
    tank_shape = CylindricalTank(115 / 2000, 0.705)

    # Define the tank
    # Since it is a massflow rate based tank this means that the mass flow rates of the liquid
    # and gas are defined by the user.
    oxidizer_tank = MassFlowRateBasedTank(
        name="oxidizer tank",
        geometry=tank_shape,
        flux_time=5.2,
        initial_liquid_mass=4.11,
        initial_gas_mass=0,
        liquid_mass_flow_rate_in=0,
        liquid_mass_flow_rate_out=(4.11 - 0.5) / 5.2,
        gas_mass_flow_rate_in=0,
        gas_mass_flow_rate_out=0,
        liquid=oxidizer_liq,
        gas=oxidizer_gas,
    )
    return oxidizer_tank
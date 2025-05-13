# Description
This replay system allows data to be played on the GCS websocket in "real time". It has the ability to play both pre and post data from previous missions or simulations. It will give a near replica of what it would be like in the field.

# Data Obtainment method
- Simulations
    - From rocketpy as of 12-05-2025
- Missions
    - From Serpentine, only current mission is 04-05-2025

# Usage
To run this code in the cli will be based on the mode seleected
`rocket replay --mode [mission|simulation]`

if mission mode is selected run
`rocket replay --mode mission --mission 20250504`

> **Note**  
> If simulation is getting errors about missing keys, it just means the current simulation data is no longer valid.  
> Run `rm -rf backend/simulation/cache`  

if simulation mode is selected run
`rocket replay --mode simulation --simulation TEST`

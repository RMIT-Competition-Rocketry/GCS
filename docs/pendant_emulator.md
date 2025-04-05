# Control Pendant Emulator

Refference schematic

![pendant_schematic](assets/pendant_schematic.png)

## Keyboard Mapping

> [!WARNING]
> This emulator always assumes that the physical translations for mechanical inputs are as follows:
> - System is always powered on, but not activated
> - Rotary is in neutral by default
> - System select is in neutral by default
> - Push in controller stick to select a mode and hold deadman to engage. This emulates the spring loaded rotary switch 

> [!CAUTION]
> Start controller in `X` mode with the switch at the front. Under no circumstances do you change this or the connection will break and a restart is required.

### Example Step By Step Guides For A Controller User

All steps require system to be on. Toggle the ON button to turn system on.

#### Uncontrolled Purge (Emergency)

1. Switch off the Raspberry Pi

#### Controlled Purge

1. Press the gas stick
2. Press the Logitec button in the middle
3. Hold gas deadman to open purge gauge

#### Fill Rocket With N2O

1. Press the gas stick
2. Press N2O
3. Hold the gas deadman to fill

#### Ignition sequence

1. Press the ignition stick
2. Hold the ignition deadman
3. Hold O2 to begin ignition
4. Hold FIRE to ignite rocket

![pendant_emulator_mapping](assets/pendant_emulator.png)

---

[Home](../README.md)

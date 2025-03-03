# Control Pendant Emulator

Refference schematic

![pendant_schematic](../notes/assets/pendant_schematic.png)

## Keyboard Mapping

> ![WARNING]
> This emulator always assumes that the physical translations for mechanical inputs are as follows:
> - Always On: POWER SWITCH (MISSLE COVER)
> - Toggle By Press: SYSTEM ACTIVE KEY SWITCH
> - Toggle By Press: GAS FILL IGINITION SELECTOR
> - Toggle by Press: GAS FILL ROTARY SWITCH 
> - Press/hold key: All momentary push buttons
> 
> - Rotary is in neutral by default
> - Gas/ignition is in gas by default
> - All other selections are False (not closed)
>
> The SPDT and rotaries swap to whatever you last pressed on. Pressing on the same option twice will not go from true to false, but will go from true to true. Likewise, if you click on gas option then click on ignition option, it will change from gas to ignition and not enable both. 
> The SPST will just be a basic on off toggle over multiple presses

> [!CAUTION]
> Start controller in `X` mode with the switch at the front. Under no circumstances do you change this or the connection will break and a restart is required.

![pendant_emulator_mapping](assets/pendant_emulator.png)

---

[Home](../README.md)
# Rocketpy Simulation Function Overview

This function is part of the RocketPy-based flight simulator and is responsible for sending simulated telemetry data to the Ground Control Station (GCS) in the form of an **AV packet**.

## Purpose

The simulaton function takes in:

- **Altitude**
- **Speed**
- **Angular velocity (w1, w2, w3)**
- **Linear acceleration (ax, ay, az)**

and prepares this data to be sent as telemetry, mimicking what would be broadcast during a real flight.

## IMPORTANT Unit Conversions (Notes to self)

- Angular velocity (`w1`, `w2`, `w3`) should be divided by **0.00875** to convert raw gyroscope data to degrees per second.
- Acceleration (`ax`, `ay`, `az`) should be divided by **9.80665** to convert from m/s² to **g**.

These conversions standardize the values for the GCS or any logging system expecting real-world units.

## 📤 Usage

This function is typically called inside `run_simulation.py`, which acts as the main simulation runner. The simulation is configured via `simulation.ini`, and this setup will be made more modular in the future.

## 🛰️ Output Format

The function prepares and transmits data as an **AV packet**, which includes **relevant (WIP, currently missing)** telemetry needed by the GCS during the simulated flight.

## ✅ TODO

The currently function of this simulator is nowhere near complete, currently working on a much larger expansion.
Current tasks in development include:

- [ ] **Modular Rocket Configuration API**  
  Develop a flexible system that can configure **any type of rocket** (solid, hybrid, liquid) using a unified structure.

- [ ] **Fuel Indication Simulation**  
  Simulate fuel levels and consumption for various propulsion systems to mirror inputs expected by the GCS.

- [ ] **Pre-Flight Check Emulation**  
  Create simulated pre-launch check routines to validate system status before ignition (e.g., sensor calibration, tank pressures, valve states).

- [ ] **Expanded Task System**  
  Enable pluggable simulation components for staging, recovery, payload deployment, etc.

- [ ] **Improve AV Packet Standardization**  
  Define a clear, versioned structure for AV packets to ensure consistent interpretation by the GCS.

---

> The function is intended to simulate live telemetry during a test run or visualization session.

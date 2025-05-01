# Display item keys and IDs
## Per module
These are the item IDs for updating values with JavaScript.

### Aux Data (aux)
| Name | Unit | API ID | API key | ID |
| --- | --- | --- | --- | --- |
| Transducer 1 | Bar | 6 | `transducer1` | `aux-transducer-1` |
| Transducer 2 | Bar | 6 | `transducer2` | `aux-transducer-2` |
| Transducer 3 | Bar | 6 | `transducer3` | `aux-transducer-3` |
| Thermocouple 1 | degC | 6 | `thermocouple1` | `aux-thermocouple-1` |
| Thermocouple 2 | degC | 6 | `thermocouple2` | `aux-thermocouple-2` |
| Thermocouple 3 | degC | 6 | `thermocouple3` | `aux-thermocouple-3` |
| Thermocouple 4 | degC | 6 | `thermocouple4` | `aux-thermocouple-4` |
| Internal temperature | degC | 7 | `internalTemp` | `aux-internaltemp` |
| Gas bottle 1 | kg | 7 | `gasBottleWeight1` | `aux-gasbottle-1` |
| Gas bottle 2 | kg | 7 | `gasBottleWeight2` | `aux-gasbottle-2` |
| Rocket load cell | kg |  |  | `aux-loadcell` |

### Avionics (av)
| Name | Unit | API ID | API key | ID |
| --- | --- | --- | --- | --- |
| GPS fix | bool | 3,4,5 | `stateFlags.GPSFixFlag` | `av-state-gpsfix` |
| Dual board state | bool | 3,4,5 | `stateFlags.dualBoardConnectivityStateFlag` | `av-state-dualboard` |
| Pyro 1 |  |  |  |`av-state-pyro-1` |
| Pyro 2 |  |  |  |`av-state-pyro-2` |
| Pyro 3 |  |  |  |`av-state-pyro-3` |
| Pyro 4 |  |  |  |`av-state-pyro-4` |
| Velocity | m/s | 3 | `velocity` | `av-velocity` |
| Mach |  | 3 | `mach_number` | `av-mach` |
| Accel X | *g* | 3 | `accelLowX, accelHighX` | `av-accel-x` |
| Accel Y | *g* | 3 | `accelLowY, accelHighY` | `av-accel-y` |
| Accel Z | *g* | 3 | `accelLowZ, accelHighZ` | `av-accel-z` |
| Gyro X | deg/s | 3 | `gyroX` | `av-gyro-x` |
| Gyro Y | deg/s | 3 | `gyroY` | `av-gyro-y` |
| Gyro Z | deg/s | 3 | `gyroZ` | `av-gyro-z` |

### Flight State (fs)
| Name | Unit | API ID | API key | ID |
| --- | --- | --- | --- | --- |
| Flight state |  | 3,4,5 | `flightState` | `fs-flightstate` |
| Time |  |  |  | `fs-time` |

### Position (pos)
| Name | Unit | API ID | API key | ID |
| --- | --- | --- | --- | --- |
| Altitude | m | 3 | `altitude` | `pos-alt-m` |
| Altitude | ft |  |  | `pos-alt-ft` |
| Max altitude | m |  |  | `pos-maxalt-m` |
| Max altitude | ft |  |  | `pos-maxalt-f` |
| GPS latitude |  | 4 | `GPSLatitude` | `pos-gps-lat` |
| GPS longitude |  | 4 | `GPSLongitude` | `pos-gps-lon` |

### Radio (radio)
| Name | Unit | API ID | API key | ID |
| --- | --- | --- | --- | --- |
| AV comms state | *bool* |  |  | `radio-av-state` |
| AV RSSI | dBm [0,255] | 3,4,5 | `meta.rssi` | `radio-av-rssi` |
| AV SNR | dB | 3,4,5 | `meta.snr` | `radio-av-snr` |
| AV Packets | *int* | 3,4,5 | `meta.packets` | `radio-av-packets` |
| GSE comms state | *bool* |  |  | `radio-gse-state` |
| GSE RSSI | dBm [0,255] | 6,7 | `meta.rssi` | `radio-gse-rssi` |
| GSE SNR | dB | 6,7 | `meta.snr` | `radio-gse-snr` |
| GSE Packets | *int* | 6,7 | `meta.packets` | `radio-gse-packets` |


## API values
### ID 3 (AV Data 1)
- meta.rssi ✅
- meta.snr ✅
- flightState ✅
- stateFlags.GPSFixFlag ✅
- stateFlags.cameraControllerConnectionFlag
- stateFlags.dualBoardConnectivityStateFlag ✅
- stateFlags.payloadConnectionFlag
- stateFlags.recoveryChecksCompleteAndFlightReady
- accelLowX ✅
- accelLowY ✅
- accelLowZ ✅
- accelHighX ✅
- accelHighY ✅
- accelHighZ ✅
- gyroX ✅
- gyroY ✅
- gyroZ ✅
- altitude ✅
- velocity ✅
- apogeePrimaryTestComplete
- apogeeSecondaryTestComplete
- apogeePrimaryTestResults
- apogeeSecondaryTestResults
- mainPrimaryTestComplete
- mainSecondaryTestComplete
- mainPrimaryTestResults
- mainSecondaryTestResults
- broadcastFlag
- mach_number ✅
​​
### ID 4 (AV Data 2)
​​
- meta.rssi ✅
- meta.snr ✅
- flightState ✅
- stateFlags.GPSFixFlag ✅
- stateFlags.cameraControllerConnectionFlag
- stateFlags.dualBoardConnectivityStateFlag ✅
- stateFlags.payloadConnectionFlag
- stateFlags.recoveryChecksCompleteAndFlightReady
- GPSLatitude ✅
- GPSLongitude ✅
​​
### ID 5 (AV Data 3)
​​
- meta.rssi ✅
- meta.snr ✅
- flightState ✅
- stateFlags.GPSFixFlag ✅
- stateFlags.cameraControllerConnectionFlag
- stateFlags.dualBoardConnectivityStateFlag ✅
- stateFlags.payloadConnectionFlag
- stateFlags.recoveryChecksCompleteAndFlightReady
​​
### ID 6 (GSE Data 1)
​​
- meta.rssi ✅
- meta.snr ✅
- stateFlags.gasFillSelected
- stateFlags.ignitionFired
- stateFlags.ingitionSelected
- stateFlags.manualPurgeActivated
- stateFlags.n20FillActiated
- stateFlags.o2FillActivated
- stateFlags.selectorSwitchNeutralPosition
- stateFlags.systemActivated
- transducer1 ✅
- transducer2 ✅
- transducer3 ✅
- thermocouple1 ✅
- thermocouple2 ✅
- thermocouple3 ✅
- thermocouple4 ✅
- errorFlags.ignitionError
- errorFlags.loadCell1Error
- errorFlags.loadCell2Error
- errorFlags.loadCell3Error
- errorFlags.loadCell4Error
- errorFlags.relay1Error
- errorFlags.relay2Error
- errorFlags.relay3Error
- errorFlags.thermocouple1Error
- errorFlags.thermocouple2Error
- errorFlags.thermocouple3Error
- errorFlags.thermocouple4Error
- errorFlags.transducer1Error
- errorFlags.transducer2Error
- errorFlags.transducer3Error
- errorFlags.transducer4Error
​​
### ID 7 (GSE Data 2)
- meta.rssi ✅
- meta.snr ✅
- stateFlags.gasFillSelected
- stateFlags.ignitionFired
- stateFlags.ignitionSelected
- stateFlags.manualPurgeActivated
- stateFlags.n20FillActivated
- stateFlags.o2FillActivated
- stateFlags.selectorSwitchNeutralPosition
- stateFlags.systemActivated
- internalTemp ✅
- windSpeed
- gasBottleWeight1 ✅
- gasBottleWeight2 ✅
- analogVoltageInput1
- analogVoltageInput2
- additionalCurrentInput1
- additionalCurrentInput2
- errorFlags.ignitionError
- errorFlags.loadCell1Error
- errorFlags.loadCell2Error
- errorFlags.loadCell3Error
- errorFlags.loadCell4Error
- errorFlags.relay1Error
- errorFlags.relay2Error
- errorFlags.relay3Error
- errorFlags.thermocouple1Error
- errorFlags.thermocouple2Error
- errorFlags.thermocouple3Error
- errorFlags.thermocouple4Error
- errorFlags.transducer1Error
- errorFlags.transducer2Error
- errorFlags.transducer3Error
- errorFlags.transducer4Error

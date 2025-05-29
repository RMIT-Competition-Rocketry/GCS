# Display item keys and IDs
## Per module
These are the item IDs for updating values with JavaScript.

### Aux Data (aux)
| Name | Unit | API ID | API key | ID | Error ID | Error Key |
| --- | --- | --- | --- | --- | --- | --- |
| Transducer 1 - N2O In | Bar | 6 | `transducer1` | `aux-transducer-1` | 6,7 | `errorFlags.transducer1Error` |
| Transducer 2 - N2O Out | Bar | 6 | `transducer2` | `aux-transducer-2` | 6,7 | `errorFlags.transducer2Error` |
| Transducer 3 - O2 | Bar | 6 | `transducer3` | `aux-transducer-3` | 6,7 | `errorFlags.transducer3Error` |
| Thermocouple 1 - N2O (int) | degC | 6 | `thermocouple1` | `aux-thermocouple-1` | 6,7 | `errorFlags.thermocouple1Error` |
| Thermocouple 2 - N2O #1 | degC | 6 | `thermocouple2` | `aux-thermocouple-2` | 6,7 | `errorFlags.thermocouple2Error` |
| Thermocouple 3 - N2O #2| degC | 6 | `thermocouple3` | `aux-thermocouple-3` | 6,7 | `errorFlags.thermocouple3Error` |
| Thermocouple 4 - O2 | degC | 6 | `thermocouple4` | `aux-thermocouple-4` | 6,7 | `errorFlags.thermocouple4Error` |
| Internal temperature | degC | 7 | `internalTemp` | `aux-internaltemp` |  |  |
| Gas bottle 1 - N2O #1 | kg | 7 | `gasBottleWeight1` | `aux-gasbottle-1` |  |  |
| Gas bottle 2 - N2O #2 | kg | 7 | `gasBottleWeight2` | `aux-gasbottle-2` |  |  |
| Rocket mass | kg | 7 | `analogVoltageInput1` | `aux-loadcell` |  |  |

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
| Nav state |  |  | `navigationStatus` | `pos-navstate` |

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

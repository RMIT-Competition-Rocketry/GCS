
# Interface items
These are the item IDs for updating values with JavaScript.

## Aux Data (aux)
| Name | Unit | API key | ID |
| --- | --- | --- | --- |
| Transducer 1 | Bar |  | `aux-transducer-1` |
| Transducer 2 | Bar |  | `aux-transducer-2` |
| Transducer 3 | Bar |  | `aux-transducer-3` |
| Thermocouple 1 | degC |  | `aux-thermocouple-1` |
| Thermocouple 2 | degC |  | `aux-thermocouple-2` |
| Thermocouple 3 | degC |  | `aux-thermocouple-3` |
| Thermocouple 4 | degC |  | `aux-thermocouple-4` |
| Internal temperature | degC |  | `aux-internaltemp` |
| Gas bottle 1 | kg |  | `aux-gasbottle-1` |
| Gas bottle 2 | kg |  | `aux-gasbottle-2` |
| Rocket load cell | kg |  | `aux-loadcell` |

## Avionics (av)
| Name | Unit | API key | ID |
| --- | --- | --- | --- |
| GPS fix | bool | `data.stateFlags.GPSFixFlag` | `av-state-gpsfix` |
| Dual board state | bool | `data.stateFlags.dualBoardConnectivityStateFlag` | `av-state-dualboard` |
| Pyro 1 | bool |  | `av-state-pyro-1` |
| Pyro 2 | bool |  | `av-state-pyro-2` |
| Pyro 3 | bool |  | `av-state-pyro-3` |
| Pyro 4 | bool |  | `av-state-pyro-4` |
| Velocity | m/s | `data.velocity` | `av-velocity` |
| Mach |  | `data.mach_speed` | `av-mach` |
| Accel X | *g* | `data.accelLowX`, `data.accelHighX` | `av-accel-x` |
| Accel Y | *g* | `data.accelLowY`, `data.accelHighY` | `av-accel-y` |
| Accel Z | *g* | `data.accelLowZ`, `data.accelHighZ` | `av-accel-z` |
| Gyro X | deg/s | `data.gyroX` | `av-gyro-x` |
| Gyro Y | deg/s | `data.gyroY` | `av-gyro-y` |
| Gyro Z | deg/s | `data.gyroZ` | `av-gyro-z` |

## Flight State (fs)
| Name | Unit | API key | ID |
| --- | --- | --- | --- |
| Flight state |  | `data.flightState` | `fs-flightstate` |
| Time |  |  | `fs-time` |

## Position (pos)
| Name | Unit | API key | ID |
| --- | --- | --- | --- |
| Altitude | m | `data.altitude` | `pos-alt-m` |
| Altitude | ft |  | `pos-alt-ft` |
| Max altitude | m |  | `pos-maxalt-m` |
| Max altitude | ft |  | `pos-maxalt-f` |
| GPS latitude |  |  | `pos-gps-lat` |
| GPS longitude |  |  | `pos-gps-lon` |

## Radio (radio)
| Name | Unit | API key | ID |
| --- | --- | --- | --- |
| AV comms state | bool |  | `radio-av-state` |
| AV RSSI |  |  | `radio-av-rssi` |
| AV SNR |  |  | `radio-av-snr` |
| AV Packets |  |  | `radio-av-packets` |
| GSE comms state | bool |  | `radio-gse-state` |
| GSE RSSI |  |  | `radio-gse-rssi` |
| GSE SNR |  |  | `radio-gse-snr` |
| GSE Packets |  |  | `radio-gse-packets` |


## Unimplemented
- `data.apogeePrimaryTestComplete`
- `data.apogeePrimaryTestResults`
- `data.apogeeSecondaryTestComplete`
- `data.apogeeSecondaryTestResults`
- `data.broadcastFlag`
- `data.mainPrimaryTestComplete`
- `data.mainPrimaryTestResults`
- `data.mainSecondaryTestComplete`
- `data.mainSecondaryTestResults`
- `data.stateFlags.cameraControllerConnectionFlag`
- `data.stateFlags.payloadConnectionFlag`
- `data.stateFlags.recoveryChecksCompleteAndFlightReady`


# Display items
These are the item IDs for updating values with JavaScript.

## Aux Data (aux)
| Name | Unit | API ID | API key | ID |
| --- | --- | --- | --- | --- |
| Transducer 1 | Bar | GSE to GCS Data 1 - ID 6 |  | `aux-transducer-1` |
| Transducer 2 | Bar | GSE to GCS Data 1 - ID 6 |  | `aux-transducer-2` |
| Transducer 3 | Bar | GSE to GCS Data 1 - ID 6 |  | `aux-transducer-3` |
| Thermocouple 1 | degC | GSE to GCS Data 1 - ID 6 |  | `aux-thermocouple-1` |
| Thermocouple 2 | degC | GSE to GCS Data 1 - ID 6 |  | `aux-thermocouple-2` |
| Thermocouple 3 | degC | GSE to GCS Data 1 - ID 6 |  | `aux-thermocouple-3` |
| Thermocouple 4 | degC | GSE to GCS Data 1 - ID 6 |  | `aux-thermocouple-4` |
| Internal temperature | degC | GSE to GCS Data 2 - ID 7 |  | `aux-internaltemp` |
| Gas bottle 1 | kg | GSE to GCS Data 2 - ID 7 |  | `aux-gasbottle-1` |
| Gas bottle 2 | kg | GSE to GCS Data 2 - ID 7 |  | `aux-gasbottle-2` |
| Rocket load cell | kg |  |  | `aux-loadcell` |

## Avionics (av)
| Name | Unit | API ID | API key | ID |
| --- | --- | --- | --- | --- |
| GPS fix | bool | AV to GCS Data 1/2 - IDs 3/4 | `data.stateFlags.GPSFixFlag` | `av-state-gpsfix` |
| Dual board state | bool | AV to GCS Data 1/2 - IDs 3/4 | `data.stateFlags.dualBoardConnectivityStateFlag` | `av-state-dualboard` |
| Pyro 1 | bool |  |  |`av-state-pyro-1` |
| Pyro 2 | bool |  |  |`av-state-pyro-2` |
| Pyro 3 | bool |  |  |`av-state-pyro-3` |
| Pyro 4 | bool |  |  |`av-state-pyro-4` |
| Velocity | m/s | AV to GCS Data 1 - ID 3 | `data.velocity` | `av-velocity` |
| Mach |  | AV to GCS Data 1 - ID 3 | `data.mach_speed` | `av-mach` |
| Accel X | *g* | AV to GCS Data 1 - ID 3 | `data.accelLowX`, `data.accelHighX` | `av-accel-x` |
| Accel Y | *g* | AV to GCS Data 1 - ID 3 | `data.accelLowY`, `data.accelHighY` | `av-accel-y` |
| Accel Z | *g* | AV to GCS Data 1 - ID 3 | `data.accelLowZ`, `data.accelHighZ` | `av-accel-z` |
| Gyro X | deg/s | AV to GCS Data 1 - ID 3 | `data.gyroX` | `av-gyro-x` |
| Gyro Y | deg/s | AV to GCS Data 1 - ID 3 | `data.gyroY` | `av-gyro-y` |
| Gyro Z | deg/s | AV to GCS Data 1 - ID 3 | `data.gyroZ` | `av-gyro-z` |

## Flight State (fs)
| Name | Unit | API ID | API key | ID |
| --- | --- | --- | --- | --- |
| Flight state |  | AV to GCS Data 1/2 - IDs 3/4 | `data.flightState` | `fs-flightstate` |
| Time |  |  |  | `fs-time` |

## Position (pos)
| Name | Unit | API ID | API key | ID |
| --- | --- | --- | --- | --- |
| Altitude | m | AV to GCS Data 1 - ID 3 | `data.altitude` | `pos-alt-m` |
| Altitude | ft |  |  | `pos-alt-ft` |
| Max altitude | m |  |  | `pos-maxalt-m` |
| Max altitude | ft |  |  | `pos-maxalt-f` |
| GPS latitude |  | AV to GCS Data 2 - ID 4 |  | `pos-gps-lat` |
| GPS longitude |  | AV to GCS Data 2 - ID 4 |  | `pos-gps-lon` |

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

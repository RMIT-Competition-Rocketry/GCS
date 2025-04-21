
# Interface items
These are the item IDs for updating values with JavaScript.

## Aux Data (aux)
| Value | Unit | id |
| --- | --- | --- |
| Transducer 1 | Bar | `aux-transducer-1` |
| Transducer 2 | Bar | `aux-transducer-2` |
| Transducer 3 | Bar | `aux-transducer-3` |
| Thermocouple 1 | degC | `aux-thermocouple-1` |
| Thermocouple 2 | degC | `aux-thermocouple-2` |
| Thermocouple 3 | degC | `aux-thermocouple-3` |
| Thermocouple 4 | degC | `aux-thermocouple-4` |
| Internal temperature | degC | `aux-internaltemp` |
| Gas bottle 1 | kg | `aux-gasbottle-1` |
| Gas bottle 2 | kg | `aux-gasbottle-2` |
| Rocket load cell | kg | `aux-loadcell` |

## Avionics (av)
| Value | Unit | id |
| --- | --- | --- |
| GPS fix | bool | `av-state-gpsfix` |
| Dual board state | bool | `av-state-dualboard` |
| Pyro 1 | bool | `av-state-pyro-1` |
| Pyro 2 | bool | `av-state-pyro-2` |
| Pyro 3 | bool | `av-state-pyro-3` |
| Pyro 4 | bool | `av-state-pyro-4` |
| Velocity | m/s | `av-velocity` |
| Accel X | *g* | `av-accel-x` |
| Accel Y | *g* | `av-accel-y` |
| Accel Z | *g* | `av-accel-z` |
| Gyro X | deg/s | `av-gyro-x` |
| Gyro Y | deg/s | `av-gyro-y` |
| Gyro Z | deg/s | `av-gyro-z` |

## Flight State (fs)
| Value | Unit | id |
| --- | --- | --- |
| Flight state | | `fs-flightstate` |
| Time | | `fs-time` |

## Position (pos)
| Value | Unit | id |
| --- | --- | --- |
| Altitude | m | `pos-alt-m` |
| Altitude | ft | `pos-alt-ft` |
| Max altitude | m | `pos-maxalt-m` |
| Max altitude | ft | `pos-maxalt-f` |
| GPS latitude |  | `pos-gps-lat` |
| GPS longitude | | `pos-gps-lon` |

## Radio (radio)
| Value | Unit | id |
| --- | --- | --- |
| AV comms state | bool | `radio-av-state` |
| AV RSSI | | `radio-av-rssi` |
| AV SNR | | `radio-av-snr` |
| AV Packets | | `radio-av-packets` |
| GSE comms state | bool | `radio-gse-state` |
| GSE RSSI | | `radio-gse-rssi` |
| GSE SNR | | `radio-gse-snr` |
| GSE Packets | | `radio-gse-packets` |
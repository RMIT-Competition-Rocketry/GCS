# System Design

**TODO**: Please formalise this at some point

![Deployment Diagram](assets/gcs_deployment_diagram.png)

There are 3 physical devices in the GCS system. The control pendant, radio and the computer. The control pendant is a physical tactile controller that operates the GSE. The radio is interchangeable between commercial solutions and SRAD solutions with a custom Hardware Abstraction Library (HAL).

## High Level Software Design

The main server in the system is responsible for reading data in from the radio and writing data back out on the radio in accordance with our SRAD networking protocols. These protocols operate on a UDP request-reply basis. The GCS will say 'do xyz and tell me what your system status is' and the device will reply back. The GCS server then broadcasts received data throughout the computer to each 'service' which are isolated programs that run completely decoupled from any other service. This architecture means that if a service was to completely and catastrophically fail, it would have no effect on any other non-dependant service. Each service would read in data from the broadcast and perform it's own computation. If a process wanted to communicate to the user, it could write data to STDOUT and the process manager system would collage each service's output onto the one terminal screen. All of the output is automatically prefixed with `DEBUG`, `INFO`, `WARNING` and `ERROR` levels, colour coded, and automatically logged to file throughout system operation.

## Service Descriptions

GCS services include the event viewer for notifying the user of GSE and avionics information whilst logging all radio packet data to a csv file for low resolution post-flight analysis. The frontend API communicates with each web client for simultaneous reading and writing of data to the web visualisation and control interface. And the pendant daemon runs in the background to poll a tactile hardware controller to send commands to the GSE such as 'fill with N2O'.

## Features

With this system, we can use any radio we want, as long as a simple hardware abstraction library can be written for it. Currently only half-duplex (1 device communicating at a time) communication is supported, but full duplex communication (2 devices communicating to each other at once) can be implemented quite easily in the future if we use 2 different frequencies. We know immediately if anything in out rocketry system is misbehaving. Avionics systems have feedback on rocketry components and much of our GSE has solenoid feed-back, thermocouples and extra monitoring features supported. All of this data is send to the GCS and presented to the operator in both the textual output and the frontend web design with visually alerting icons and warning messages. This allows us to troubleshoot easily and make GO/NO-GO calls confidently.

Many primitive monitoring applications show everything. Our system understands that not everything is important. There is no need to show the reading of every sensor as soon as you receive information. Our system only shows information that may be useful to the operator to reduce clutter and response time. All of the data appears in real time. We can see as soon as the rocket is ready for ignition, or as soon the rocket has hit apogee. As our system also connects to our GSE and offers a web interface, we can present real time GSE feedback to pad personnel on a tablet out near the launch rail This system will work seamlessly for any vehicle that has an Australis flight computer or follows the Australis networking protocol. Various settings and models may need to be updated to fit each rocket's flight profile.

<!-- ---

WIP

see working changes on [master design Excalidraw file](https://github.com/RMIT-Competition-Rocketry/GCS/blob/main/docs/assets/master-design.excalidraw) -->

---

[Home](../README.md)

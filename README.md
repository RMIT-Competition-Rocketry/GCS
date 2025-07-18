<img height=200px src="docs/assets/graphical-banner.png">

<img alt="Static Badge" src="https://img.shields.io/badge/note-Temporarily_archived-9e6a05">

<p>
    <img src="https://raw.githubusercontent.com/RMIT-Competition-Rocketry/.github/refs/heads/main/assets/hive_badge.svg" height="20rem">
    <img alt="Static Badge" src="https://img.shields.io/badge/status-Deployed_for_IREC-limegreen">
    <img src="https://github.com/RMIT-Competition-Rocketry/GCS/actions/workflows/build_and_test_cpp.yml/badge.svg" height="20rem">
    <!-- <img src="https://img.shields.io/github/v/release/RMIT-Competition-Rocketry/GCS?label=version" height="20rem"> -->
</p>

![banner](docs/assets/banner.png)

Repository for RMIT HIVE's rocketry GCS (**Ground Control Station**). 

**Named after Soteria, the Greek goddess of safety and deliverance from harm.**

> [!WARNING]
> This repository is archived in it's 2025 IREC state. Development of the 2026 IREC GCS is ongoing in a private repo. When it is done it will be merged back into this repository. Updates will be posted on [Freddy's Linkedin](https://www.linkedin.com/in/freddy-mcloughlan/) over the next year.

<p align="center">
  <img src="docs/assets/serp2launchSetup.jpg" height="200px"/>
  <img src="docs/assets/serp2launch.jpg" height="200px">
</p>
<p align="center">
  <img src="docs/assets/irec2025stand.jpeg" height="250px"/>
</p>

© 2025 RMIT Competition Rocketry - Licensed under the MIT License    

## Contents

### Documentation

- [Setup](docs/setup.md)
- [Usage](docs/usage.md)
- [Pendant Emulator Quick Reference](docs/pendant_emulator.md)
- [System Design & features](docs/system_design.md)
- [Development](docs/development.md)
- [Glossary](docs/glossary.md)

<!-- ### Notes

- [Brainstorming](notes/brainstorming.md)
- [Data](notes/data.md) -->


## Description

The GCS, known as SOTERIA, is HIVE's computer control system for GSE control, avionics communication, and data visualisation. The core of the GCS is a single computer running SRAD software with SRAD LoRa radio hardware peripherals. All OSI layers in our networking stack above the physical protocol are SRAD for use with our Australis (avionics) ecosystem. The software converts raw serial input from physical radio interfaces into human-readable output for efficient system monitoring by the GCS operator and visualisations for observers. We use a WebSocket and a protocol buffer based IPC API to communicate with our GCS services. Our web frontend is fully SRAD aside from industry-standard libraries. The GCS operator can see if any system is performing sub-optimally via alert and warning readouts, so they can make an informed GO/NO-GO call quickly. Spectators and other team members have access to several different views detailing all telemetry from both the GSE and avionics systems

## Credit

GCS Software Team

| Name | Role | Year |
| --- | --- | --- |
| [Freddy Mcloughlan](https://www.linkedin.com/in/freddy-mcloughlan/) (`mcloughlan`)  | GCS software lead & backend software engineer | 2025 |
| [Amber Taylor](https://www.linkedin.com/in/amber-taylor-20bb63264/) (`s4105951`)  | GCS frontend lead & software engineer | 2025 |
| [Caspar O'Neill](https://www.linkedin.com/in/caspar-oneill/) (`s3899921`)  | GCS frontend API engineer | 2025 |
| [Anuk Jayasundara](https://www.linkedin.com/in/anuk-jayasundara-ab440b1aa/) (`s3899921`)  | GCS 6DOF rocket visualisation | 2025 |
| Jonathan Do (`s4003025`)  | GCS frontend UI/UX design | 2025 |
| Nathan La (`s4003562`)  | GCS data visualisation | 2025 |
| [Tristan Le](https://www.linkedin.com/in/trist4nl3/) (`trist4nl3`) | GCS simulation integration | 2025 |

Special thanks

- [Jonathan Chandler](https://www.linkedin.com/in/jonathan-chandler-03474b1ba/)
    - GCS Lead. The all-knowing being of ground control and operations
- [Matthew Ricci](https://www.linkedin.com/in/matthewricci-embedded/)
    - Flight computer [avionics firmware](https://github.com/RMIT-Competition-Rocketry/Australis-Avionics-firmware) lead.

And to all those at RMIT HIVE!

## Software Development Components

This project was built using the following tools, languages and systems.

- Radio commuincation:
    - [LoRa](https://en.wikipedia.org/wiki/LoRa) with both COTS and SRAD hardware
- Multithreaded data ingestion server
    - Written in C++
    - Built with [ZeroMQ](https://zeromq.org/) for IPC communication
    - IPC Data serialisation with [Google's Protocol Buffers](https://protobuf.dev/)
- Multithreaded CLI based process manager
    - Written in Python
    - Includes a device emulator for internal system tests that attaches from the hardware layer to create a fake unix device file at `/dev/`

**Cool fact**: Our GCS runs at less than 1% CPU utilization on a Raspberry Pi 5 during regular use.

## Screenshots

![GUI interface](docs/assets/frontend-example.png)

> Web interface (main view)

![HMI page](docs/assets/hmi-example.png)

> Custom GSE HMI page

![CLI interface](docs/assets/cli.png)

> CLI (nobody but me looks at this)

## License and Attribution

This project is licensed under the MIT License.

If you use or modify this software, you **must retain** the original copyright
notice and license in all copies or substantial portions of the Software.

Attribution must be clearly displayed in any redistributed or derivative works.

Please credit: **RMIT Competition Rocketry** and the **HIVE GCS Software Team**.

See the [LICENSE](LICENSE) file for full terms.

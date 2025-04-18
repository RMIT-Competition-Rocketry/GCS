# GCS

<p>
    <img src="https://raw.githubusercontent.com/RMIT-Competition-Rocketry/.github/refs/heads/main/assets/hive_badge.svg" height="20rem">
    <img alt="Static Badge" src="https://img.shields.io/badge/status-work_in_progress-orange">
    <img src="https://github.com/RMIT-Competition-Rocketry/GCS/actions/workflows/build_and_test_cpp.yml/badge.svg" height="20rem">
</p>

Code repository for RMIT HIVE's IREC competition team rocket GCS (**Ground Control Station**) data ingestion and visulisation software.

🇦🇺 🦘 

<!-- TODO Make a monochrome png for logos. Consider https://simpleicons.org/ -->

<p >
    <img src="docs/assets/hive-logo.png" alt="HIVE Logo" height="50">
    <img src="docs/assets/RMIT_University_Logo.png" alt="RMIT Logo" height="50" style="padding-left:10px">
    <img src="docs/assets/IREC.jpg" alt="IREC Logo" height="50" style="padding-left:10px">
</p>


## Credit

| Name | Role | Year |
| --- | --- | --- |
| Freddy Mcloughlan (`mcloughlan`)  | GCS backend software engineer | 2025 |
| Amber Taylor (`s4105951`)  | GCS frontend developer | 2025 |
| Caspar O'Neill (`s3899921`)  | GCS QA engineer & API integration | 2025 |
| Anuk Jayasundara (`s3899921`)  | GCS frontend developer | 2025 |
| Nathan La (`s4003562`)  | GCS data visualisation programmer | 2025 |
| Jonathan Do (`s4003025`)  | GCS UI/UX Designer | 2025 |

---

<!-- https://github.com/Ileriayo/markdown-badges -->

## Contents

### Documentation

- [Setup](docs/setup.md)
- [Usage](docs/usage.md)
- [Pendant Emulator Quick Refference](docs/pendant_emulator.md)
- [Application Layers](docs/application_layers.md)
- [Development](docs/development.md)
- [Glossary](docs/glossary.md)

### Notes

- [Brainstorming](notes/brainstorming.md)
- [Data](notes/data.md)

---

## Development components

This project was built using the following tools, languages and systems.

- Radio commuincation:
    - [LoRa](https://en.wikipedia.org/wiki/LoRa) with both COTS and SRAD hardware
- Multithreaded data ingestion server
    - Written in C++
    - Built with [ZeroMQ](https://zeromq.org/) for IPC communication
    - IPC Data serialisation with [Google's Protocol Buffers](https://protobuf.dev/)
- Multithreaded CLI based process manager
    - Written in Python
    - Includes a device emulator for internal unit tests that attaches from the hardware layer to create a fake unix device file at `/dev/`


![CLI interface](docs/assets/cli.png)

Example CLI interface using [retro term](https://github.com/Swordfish90/cool-retro-term) because it's cool. Front end interface will be added before competing

# Application Layers

This document details the high level modularisation of data processes for the back end software.

The rationale for a layered design is to account for the changing requirements of the data transmission system for the GSE and avionics systems. Intitial setups will use a LoRa breakout board with AT commands over UART and final designs aim to use a custom SRAD (Student Researched And Developed) protocol over ISA. Different protocols with different hardware and software protocols are better managed and more easily maintained with this layered setup. 

<!-- TODO: Insert Excalidraw (notes/assets/application_layer_diagram.excalidraw-something) image -->

## Driver ('hardware') Layer

This layer is responsible for:

- Handling kernel level IO operations with the device
- Exposing a device node abstraction in the `/dev/` directory

It's expected at the time of writing that drivers will be available for all devices we will be using. If I end up writing my own I will update this section

## Middleware Layer

This layer is responsible for:

- Low level bit manipulation not handled in the driver
- Exposing a unix socket for IPC
    - Formalising IPC communication with the socket
    - Error correction and validation with retries if needed
- Device management 
- Logging

## Application Layer

This layer is responsible for:

- Connecting to the middleware socket for:
    - Data parsing
    - Packet aggregation and formal data object creation
- Exporting data to the database

This layer also includes the CLI script which will start and display logs of each proccess.

---

[Home](../README.md)
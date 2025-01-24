# Packet and commuincation notes

## Development roadmap

Commuincation will start with and go in order of

1. Raspi + E5 LoRa breakout
    - White Cliffs
    - UART AT Commands
        - Writing to the [E5 LoRa breakout board](https://core-electronics.com.au/makerverse-lora-e5-breakout-module.html) will be with [AT commands](https://files.seeedstudio.com/products/317990687/res/LoRa-E5+AT+Command+Specification_V1.0+.pdf). Particularly [test mode](https://files.seeedstudio.com/products/317990687/res/LoRa-E5+AT+Command+Specification_V1.0+.pdf#page=52)
1. Raspi + SRAD LoRa
    - Use when ready to progress from previous setup
    - UART SRAD undefined Protocol
        - Writing to SRAD is undefined protocol. Could just be raw packet with start and end byte. That is that the data layout in the payload is not defined with any structure as of yet.
1. PCM SRAD LoRa
    - America
    - ISA with UART fallback. Both using SRAD undefined Protocol

## Sequence diagram

![sequence diagram](assets/sequence_diagram.png)

> [!NOTE]  
> Note that data trasmmission in the sequence diagram is abstracted and data in those transmissions can and may be multiple sequential packets of different structures. Make this robust in the software design.

## RX Brainstorming Summary

In the final design data will come from the LoRa module and then you will get a raw packet of 16 bytes via I2C or ISA what comes directly to the PCM via GPIO. This will require a linux driver or parser script.

The strcuture of those 16 bytes will be determined by the team. See the [LoRa design spreadsheet](https://rmiteduau-my.sharepoint.com/:x:/r/personal/s3783701_student_rmit_edu_au/_layouts/15/Doc.aspx) or the image below. They have a bunch of cells explaining each byte. There is discussion on how the packet design will work. Multiple sequential packets will need to be sent when data overflows 16 bytes. This applies to TX and RX, noting that commuincation is also half duplex.

![packet payload design](assets/payload_prelim.png)

So make sure your design defines objects that are easily configurable to account for changed in packet payload structure. 

Then you can pull apart those packets and dump them stright into the database.

once we are on PCM, it must be a C type driver for initial data ingestion. I guess. 

### RX Prelminary Understadning

Data enters the computer via I2C or ISA (configurable via a settings file) and then that data goes into a C driver for the respective data method. The driver applies bit masks and possibly bit banging. The driver then exposes that data via `/dev/my_isa_or_i2c_device` as a device node abstraction which isn't an actual file. Then the middleware layer (also in C) performs reads and writes through the device node to get the packet data raw (minus masks and banging). Then that data is exposed again through a socket file. Then the application layer attaches to the socket file and does the final parsing and writes it all to a local database. 

Meanwhile, each proccess is monitored with a CLI logging application. 

### Hardware Input

![Hardware pendant schematic](assets/pendant_schematic.png)

The hardware input will come from a pendant that will have digital inputs sent to a GPIO array on the PCM. The design includes saftey checks with GPIO0/1 as that it must be high or low (forgot which one, see diagram) to indicate that the input is healthy. A flipped bit in this channel may indicate an issue with the hardware. 

Then you will need to write this data to the rocket as well.
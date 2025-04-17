# Usage

> [!IMPORTANT]
> Please ensure you have seen the [setup instructions](setup.md) before running the software.

Run the following for CLI help

```terminal
$ rocket --help
Usage: rocket [OPTIONS] COMMAND [ARGS]...

  CLI interface to manage GCS software initialisation

Options:
  --help  Show this message and exit.

Commands:
  dev         Start software in development mode
  run         Start software for launch day usage
  simulation  Start software in simulation mode
```

> [!IMPORTANT]
> Before running in release mode (`$ rocket run`), if you have not generated protobuf files previously you need to run `$ bash scripts/proto_manual.sh`.
> 
> Before [#29](https://github.com/RMIT-Competition-Rocketry/GCS/issues/29) is closed, you will need to keyboard intterupt when you want to close it.


> [!NOTE] 
> The current *suggested* frontend dev command is as follows
> ```
> $ rocket simulation --interface test --nopendant    
> ```

## Using release binaries

If you plan to use a pre-compiled binary, please place it in the root directory of the project.

## Usage for developers

For development, `dev` mode is available

```terminal
$ rocket dev --help
Usage: rocket dev [OPTIONS]

  Start software in development mode

Options:
  --docker                 Run inside Docker
  --interface [UART|TEST]  Hardware interface type. Overrides config parameter
  --nobuild                Do not build binaries. Search for pre-built
                           binaries
  --logpkt                 Log packet data to csv
  --nopendant              Do not run the pendant emulator
  --help                   Show this message and exit.
```

By default for `dev` mode: 
- The selected interface will be grabbed from `config/config.ini`
  - Unless `--interface` is passed which will override this
- Cmake and make will rebuild the project
  - Use `--nobuild` to skip this
- Packets will not be logged in `/logs`, but the CLI output will
  - Use `--logpkt` to log packets in dev mode
- The pendant emulator will start in a new window
  - This is not needed for **frontend** development
  - You can stop this by using the `--nopendant` flag

### Simulation Mode

Simulation mode can be run with 

```terminal
$ rocket simulation --interface test <options>
```

This operates the same as dev mode, but will use simulation based data 

> [!WARNING]
> Currently, this mode only **simulates** AVtoGCSData1 packets from ignition to landing.
> 
> Options are being developed to replay preivous flights. We still need to fly at least once for this

## Usage for operators

```terminal
$ rocket run --help
Usage: rocket run [OPTIONS]

  Start software for production usage in native environment. Indented for
  usage on GCS only

Options:
  --help  Show this message and exit.
```

1. If you have not downloaded a release binary, you can create one with `$ bash scripts/release.sh`
2. To start the software from the project directory, run the command `$ rocket run`
3. To stop the software, enter <kbd>ctrl</kbd> + <kbd>c</kbd> on the pendant emulator window (if it has started) then in the other window after the emulator window has shut down. 
 
---

[Home](../README.md)

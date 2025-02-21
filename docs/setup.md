
# Setup

The GSE software is run by using a Python based CLI. 

## Prerequisites

> [!NOTE]
> Items denoted with 🐳 are installed in the Docker container. They do not require manual installation.

**TODO: update this when you do the first fresh install**

| Software   | Must have | Docker Dev  | Native Dev |
|---------------|----------|--------------------|--------------------|
| Python >= 3.10 | ✅        | ✅                  | ✅                  |
| Docker        | ❌       | ✅                  | ❌                  |
| Socat         | ❌        |  🐳                 | ✅                  |
| g++ |✅|🐳|✅|
| [ZeroMQ](https://zeromq.org/download/) |✅|🐳|✅| 
| Protobuf |✅|🐳|✅| 

## Setup Instructions

Firstly navigate into this repository directory and ensure you have Python 3 installed

```shell
$ python3 --version
```

Then install the necessary packages

```shell
$ python3 -m pip install -r requirements.txt
```

> [!NOTE]
> These packages are required for CLI usage and the production environment of the software. Testing packages are installed in the Docker container only

And run the setup script to make the CLI file executable.

```shell
$ bash setup.sh
```

> [!NOTE]
>  Otherwise you can run the CLI with `$ python3 rocket.py --args` in place of all further refferences of `$ rocket --args` if you don't run the setup file.

## Testing Setup

Please install [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) or [Docker Engine](https://docs.docker.com/engine/install/) on your system. Install the desktop version if you would like a GUI.

## Further Steps

See [usage](usage.md)

---

[Home](../README.md)
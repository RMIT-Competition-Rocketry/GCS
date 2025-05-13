
# Setup

The GCS software is run by using a Python based CLI with a C++ server component. There are several dev tools used for testing included in the dependencies as well

## Prerequisites

> [!NOTE]
> Items denoted with 🐳 are installed in the Docker container. They do not require manual installation.
> Items denoted with 🟨 are not required if you use release binaries. Install these if you want to build yourself with debug binaries

> [!NOTE]
> *Protobuf gencode without building can be done by running the proto script in `scripts/`.
> 
> Some C++ libraries have untested `FetchContent` support for cmake. This means you may be able to build after installing just CMake. Provided you are connected to internet to download those packages. Currently they do not work. Protobuf is a pain in the ass to work with.
>
> Also running setup.sh will install Protobuf automatically

| Software | Version | Release Mode Only | Docker Dev | Native Dev |
| --- | --- | --- | --- | --- |
| Python | `3.11.x` | ✅ | ✅ | ✅ |
| Docker | | ❌ | ✅ | ❌ |
| Socat | Latest? | ❌ | 🐳 | ✅ |
| Cmake | >=`3.25` | ❌ | 🐳 | 🟨 |
| g++ or clang++ | Untested | ❌ | 🐳 | 🟨 - needed if you don't have Protobuf |
| [ZeroMQ](https://zeromq.org/download/) | `4.3.x` | ❌? | 🐳 | 🟨 |
| cppzmq | `4.10.x` | ❌? | 🐳 | 🟨 |
| Abseil libraries | `20250127.x` | ❌? | 🐳 | 🟨 |
| Protobuf* (inc. `proto` compiler & `libprotodev`) | `30.x` | ✅ (_needed for gencode_) | 🐳 | ✅ |
| qrencode | Latest? | ✅ | 🐳 | ✅ |
| pytest | Latest? | _for testing_ | 🐳 | _for testing_ |

> [!WARNING]
> Please let me know if this is wrong. I may have missed some things

Building all from source can be found the `build.yml` action.

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

And run the setup script to make aliases, setup permissions and install protobuf.

```shell
$ bash setup.sh
```

> [!NOTE]
>  Otherwise you can run the CLI with `$ python3 rocket.py <args>` in place of all further refferences of `$ rocket --args` if you don't run the setup file.

## Further Steps

See [usage](usage.md)

---

[Home](../README.md)

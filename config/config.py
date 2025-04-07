from configparser import ConfigParser
from typing import Dict
import os
import platform


def get_default_config_path():
    """
    Get absolute path based on where you're running the script.
    This is just stupid hard code because the hardware pendant is in a seperate environment.
    Can remove this crap when you don't need pendant emulator anymore.
    """
    system = platform.system()
    if system == 'Darwin':
        return "/Users/freddy/Desktop/Stuff/Code_Local/Rocket/config/config.ini"
    elif system == 'Linux':
        return "/home/rmit/GCS/config/config.ini"
    else:
        raise NotImplementedError(f"Unsupported OS: {system}")


def load_config(file_path=get_default_config_path()) -> Dict[str, str]:
    """Loads configuration settings from an INI file.

    Args:
        file_path (str): Path to the .ini configuration file.

    Returns:
        dict[str, str]: A dictionary containing configuration settings.
    """
    config = ConfigParser()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found: {file_path}")
    config.read(file_path)

    return config

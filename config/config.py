from configparser import ConfigParser
from typing import Dict
import os


def get_default_config_path():
    """
    Get absolute path based on where you're running the script.
    This is just stupid hard code because the hardware pendant is in a seperate environment/process.
    Can remove this crap when you don't need pendant emulator anymore.
    """
    CONFIG_LOCATOR_FILE = os.path.join(
        os.path.sep, "tmp", "GCS_CONFIG_LOCATION.txt")
    if os.path.exists(CONFIG_LOCATOR_FILE):
        with open(CONFIG_LOCATOR_FILE, "r") as f:
            return f.read().strip()

    return os.path.join(os.getcwd(), "config", "config.ini")


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

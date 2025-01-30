from configparser import ConfigParser
from typing import Dict


def load_config(file_path="backend/config.ini") -> Dict[str, str]:
    """Loads configuration settings from an INI file.

    Args:
        file_path (str): Path to the .ini configuration file.

    Returns:
        dict[str, str]: A dictionary containing configuration settings.
    """
    config = ConfigParser()
    config.read(file_path)

    return config

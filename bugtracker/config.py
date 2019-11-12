import os
import json


def load(config_path):
    """
    This function provides a simple way to call load a .json
    config file.

    One weakness of this approach is that the top-level scripts
    must be run from within the /apps folder.
    """

    if not os.path.isfile(config_path):
        raise FileNotFoundError(config_path)

    config_file = open(config_path, mode='r')
    config_json = json.load(config_file)
    config_file.close()

    return config_json
import os
import sys
import json
import pathlib
from contextlib import contextmanager

@contextmanager
def suppress_stdout():
    with open(os.devnull, 'w') as devnull:
        valid_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = valid_stdout

with suppress_stdout():
    import pyart

import bugtracker.config


def generate_config():
    """
    Create a config file that is rooted in some user-specified
    directory.
    """

    print("Specify a directory for Bugtracker application data:")
    bugtracker_root = input(">")
    
    # Check if parent directory exists
    root_path = pathlib.Path(bugtracker_root)
    parent = root_path.parent

    if not os.path.isdir(parent):
        raise FileNotFoundError(f"Path parent does not exist: {parent}")

    if not os.path.isdir(bugtracker_root):
        os.mkdir(bugtracker_root)

    output_json = os.path.join("apps", "bugtracker.json")

    template = bugtracker.config.ConfigTemplate()
    template.populate(bugtracker_root)
    print("template data:")
    print(template.data)
    template.write(output_json)
    template.make_folders()


if __name__ == "__main__":
    generate_config()
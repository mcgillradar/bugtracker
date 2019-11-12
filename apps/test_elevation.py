"""
Throwaway code to test the elevation.
"""

import os
import sys
import math
import datetime
import argparse
from contextlib import contextmanager

import numpy as np

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

import bugtracker



def main():
    
    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    reader = bugtracker.calib.elevation.SRTM3Reader(metadata, grid_info)

    reader.get_active_cells()
    keys = reader.get_active_keys()
    print(keys)

    elevation = reader.load_elevation()

    # Plot elevation


main()
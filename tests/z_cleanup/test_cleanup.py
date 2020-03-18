"""
The z_ prefix is just a dumb trick to get the pytest
framework to execute this set of tests last. The role
of these tests is to ensure that all of the files generated
during the unit testing get deleted.
"""

import os
import glob

import pytest

import bugtracker


def test_clear_calib():
    """
    Clear calibration files
    """

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    cache_dir = config["cache_dir"]
    calib_dir = os.path.join(cache_dir, "calib")

    calib_files = glob.glob(os.path.join(calib_dir, "*.nc"))

    for calib_file in calib_files:
        os.unlink(calib_file)

    calib_files = glob.glob(os.path.join(calib_dir, "*.nc"))

    assert len(calib_files) == 0

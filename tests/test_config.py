import os

import pytest

import bugtracker


def test_check_exists():
    """
    Check if the config file exists.
    """

    config_path = "../apps/bugtracker.json"
    assert os.path.isfile(config_path)


def test_fields():
    """
    Check all fields exist.
    Check that all folders exist.
    """

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    folders = ["plot_dir", "netcdf_dir", "cache_dir", "animation_dir"]
    for folder in folders:
        assert folder in config
        assert os.path.isdir(config[folder])

    iris_keys = ["convol_scans"]
    clutter_keys = ["dbz_threshold", "coverage_threshold"]
    precip_keys = ["azim_region", "gate_region", "max_dbz_per_degree"]

    for key in iris_keys:
        assert key in config["iris_settings"]

    for key in clutter_keys:
        assert key in config["clutter"]

    for key in precip_keys:
        assert key in config["precip"]
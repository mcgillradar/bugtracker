import os

import pytest

import bugtracker


def test_check_exists():
    """
    Check if the config file exists.
    """

    config_path = "../apps/bugtracker.json"
    assert os.path.isfile(config_path)


def test_missing_file():
    """
    Verify FileNotFoundError
    """

    missing_config_path = "../nonexistant/relative/file/path/"
    with pytest.raises(FileNotFoundError):
        config = bugtracker.config.load(missing_config_path)


def test_fields():
    """
    Check all fields exist.
    Check that all folders exist.
    """

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    folders = ["archive_dir", "plot_dir", "cache_dir"]
    for folder in folders:
        assert folder in config
        assert os.path.isdir(config[folder])

    keys = ["iris_convol_scans", "clutter", "precip"]

    for key in keys:
        assert key in config

    clutter_keys = ["dbz_threshold", "coverage_threshold"]
    precip_keys = ["azim_region", "gate_region", "max_dbz_per_degree"]

    for key in clutter_keys:
        assert key in config["clutter"]

    for key in precip_keys:
        assert key in config["precip"]
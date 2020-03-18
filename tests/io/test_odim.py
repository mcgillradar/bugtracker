import pytest

import bugtracker


def test_odim_sample():

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    odim_data = bugtracker.core.samples.odim_sample(config)

    assert odim_data.dbz_unfiltered is not None

    dbz_shape = odim_data.dbz_unfiltered.shape

    expected_angles = 6
    expected_azims = 720
    expected_gates = 480

    assert dbz_shape[0] == expected_angles
    assert dbz_shape[1] == expected_azims
    assert dbz_shape[2] == expected_gates
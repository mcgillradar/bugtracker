import pytest

import bugtracker


def test_odim_sample():

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    odim_data = bugtracker.core.samples.odim_sample(config)

    assert odim_data.dbz_unfiltered is not None

    dbz_shape = odim_data.dbz_unfiltered.dbz_shape

    assert dbz_shape[0] == 720
    assert dbz_shape[1] == 1823
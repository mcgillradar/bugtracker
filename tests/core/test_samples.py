import os
import datetime

import bugtracker


def test_metadata():
    """
    Test Metadata sample generation
    """

    metadata = bugtracker.core.samples.metadata()

    assert isinstance(metadata, bugtracker.core.metadata.Metadata)
    assert metadata.lat == 44.45
    assert metadata.lon == -110.081


def test_grid_info():
    """
    Test GridInfo sample generation
    """

    grid_info = bugtracker.core.samples.grid_info()

    assert isinstance(grid_info, bugtracker.core.grid.GridInfo)
    assert grid_info.azims == 720
    assert grid_info.gates == 512
    assert grid_info.azim_step == 0.5
    assert grid_info.gate_step == 500.0


def test_sin_dbz():
    """
    Test radially sinusoidal sample pattern
    """

    grid_info = bugtracker.core.samples.grid_info()
    sin_dbz = bugtracker.core.samples.sin_dbz(grid_info)

    dims = (grid_info.azims, grid_info.gates)
    assert sin_dbz.shape == dims
    assert sin_dbz.dtype == float


def test_iris_set():
    """
    Test the existance of every file in iris_set
    """

    config = bugtracker.config.load("../apps/bugtracker.json")
    iris_set_xam = bugtracker.core.samples.iris_set_xam(config)
    iris_set_wgj = bugtracker.core.samples.iris_set_wgj(config)

    test_sets = [iris_set_xam, iris_set_wgj]

    for test_set in test_sets:
        assert isinstance(test_set.datetime, datetime.datetime)
        assert os.path.isfile(test_set.convol)
        assert os.path.isfile(test_set.dopvol_1A)
        assert os.path.isfile(test_set.dopvol_1B)
        assert os.path.isfile(test_set.dopvol_1C)
        assert os.path.isfile(test_set.dopvol_2)

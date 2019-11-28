import datetime

import numpy as np
import pyart
import pytest

import bugtracker


def test_generate_radar():
    """
    Test generating radar object from pyART from GridInfo
    """

    grid_info = bugtracker.core.samples.grid_info()
    metadata = bugtracker.core.samples.metadata()
    dbz_array = np.zeros((720,512), dtype=float)

    pyart_radar = grid_info.create_radar(dbz_array, metadata)
    assert isinstance(pyart_radar, pyart.core.radar.Radar)


def test_invalid_dims():
    """
    Test generation of invalid dims, should raise ValueError
    """

    grid_info = bugtracker.core.samples.grid_info()
    metadata = bugtracker.core.samples.metadata()
    wrong_azims = np.zeros((999,512), dtype=float)

    # Test with wrong number of azims
    with pytest.raises(ValueError):
        pyart_radar = grid_info.create_radar(wrong_azims, metadata)

    wrong_gates = np.zeros((720,999), dtype=float)

    # Test with wrong number of gates
    with pytest.raises(ValueError):
        pyart_radar = grid_info.create_radar(wrong_gates, metadata)

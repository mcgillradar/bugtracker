import bugtracker


def test_clutter_filter():
    """
    Test creation of a clutter filter
    """

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    clutter_filter = bugtracker.calib.clutter.ClutterFilter(metadata, grid_info)

    angles = [-0.5, -0.3, -0.1, 0.1, 0.3]
    clutter_filter.setup(angles)
    filter_dims = (len(angles), grid_info.azims, grid_info.gates)

    assert filter_dims == clutter_filter.filter_3d.shape
    assert clutter_filter.filter_3d.sum() == 0

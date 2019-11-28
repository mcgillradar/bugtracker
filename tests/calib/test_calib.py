import bugtracker


def test_controller():

    metadata = None
    gates = 512
    azims = 720
    gate_step = 500
    azim_step = 0.5
    grid_info = bugtracker.core.grid.GridInfo(gates, azims, gate_step, azim_step)
    controller = bugtracker.core.calib.CalibController(metadata, grid_info, 'iris')

    controller.geometry_mask()
    controller.clutter_mask()

    test_dims = (azims, gates)

    assert controller.calib_data.geometry_mask.shape == test_dims
    assert controller.calib_data.clutter_mask.shape == test_dims
import os
import datetime

import bugtracker

class CalibArgs:

    def __init__(self, timestamp, data_hours, station):
        self.timestamp = timestamp
        self.data_hours = data_hours
        self.station = station


def test_iris_calib():

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    
    # For testing, only take 1 hour
    data_hours = 1
    station = metadata.radar_id

    fmt = "%Y%m%d%H%M"
    calib_time = datetime.datetime(2013, 7, 14, 12, 0, 0)
    calib_timestamp = calib_time.strftime(fmt)

    args = CalibArgs(calib_timestamp, data_hours, station)

    iris_dir = os.path.join(config['input_dirs']['iris'], "xam")
    iris_collection = bugtracker.io.iris.IrisCollection(iris_dir, "xam")
    if len(iris_collection.sets) == 0:
        raise ValueError("Invalid length")

    calib_grid = bugtracker.calib.calib.get_srtm(metadata, grid_info)

    calib_controller = bugtracker.calib.calib.IrisController(args, metadata, grid_info)
    calib_controller.set_grids(calib_grid)

    data_mins = args.data_hours * 60

    calib_sets = iris_collection.time_range(calib_time, data_mins)

    threshold = config['clutter']['coverage_threshold']

    calib_controller.set_calib_data(calib_sets)
    calib_controller.create_masks(threshold)
    calib_controller.save()
    calib_controller.save_masks()

    calib_path = bugtracker.core.cache.calib_filepath(metadata, grid_info)
    assert os.path.isfile(calib_path)
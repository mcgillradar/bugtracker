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

    iris_collection = bugtracker.io.iris.IrisCollection("xam")

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


def test_nexrad_calib():

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    # For testing, only take 1 hour
    data_hours = 1
    station = "kcbw"

    date_format = "%Y%m%d%H%M"
    calib_time = datetime.datetime(2019, 7, 14, 2, 0, 0)
    calib_timestamp = calib_time.strftime(date_format)

    args = CalibArgs(calib_timestamp, data_hours, station)

    # Filtering input arguments
    station_id = args.station.strip().lower()
    start_time = datetime.datetime.strptime(args.timestamp, date_format)
    end_time = start_time + datetime.timedelta(hours=args.data_hours)

    start_string = start_time.strftime(date_format)
    end_string = end_time.strftime(date_format)
    print(f"NEXRAD calibration time range {start_string}-{end_string}")

    # Initializing manager class
    manager = bugtracker.io.nexrad.NexradManager(config, station_id)
    manager.populate(start_time)

    calib_grid = bugtracker.calib.calib.get_srtm(manager.metadata, manager.grid_info)

    calib_files = manager.get_range(start_time, end_time)

    for calib_file in calib_files:
        if not os.path.isfile(calib_file):
            raise FileNotFoundError(calib_file)

    threshold = config['clutter']['coverage_threshold']

    calib_controller = bugtracker.calib.calib.NexradController(args, manager)
    calib_controller.set_grids(calib_grid)
    calib_controller.set_calib_data(calib_files)
    calib_controller.create_masks(threshold)
    calib_controller.save()
    calib_controller.save_masks()

    calib_path = bugtracker.core.cache.calib_filepath(manager.metadata, manager.grid_info)
    assert os.path.isfile(calib_path)


def test_odim_calib():

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    
    # For testing, only take 1 hour
    data_hours = 1
    station = "casbv"

    date_format = "%Y%m%d%H%M"
    calib_time = datetime.datetime(2020, 2, 19, 2, 0, 0)
    calib_timestamp = calib_time.strftime(date_format)

    args = CalibArgs(calib_timestamp, data_hours, station)

    # Filtering input arguments
    station_id = args.station.strip().lower()
    start_time = datetime.datetime.strptime(args.timestamp, date_format)
    end_time = start_time + datetime.timedelta(hours=args.data_hours)

    start_string = start_time.strftime(date_format)
    end_string = end_time.strftime(date_format)
    print(f"ODIM calibration time range {start_string}-{end_string}")

    # Initializing manager class
    manager = bugtracker.io.odim.OdimManager(config, station_id)
    manager.populate(start_time)

    calib_grid = bugtracker.calib.calib.get_srtm(manager.metadata, manager.grid_info)

    calib_files = manager.get_range(start_time, end_time)

    for calib_file in calib_files:
        if not os.path.isfile(calib_file):
            raise FileNotFoundError(calib_file)

    threshold = config['clutter']['coverage_threshold']

    calib_controller = bugtracker.calib.calib.OdimController(args, manager)
    calib_controller.set_grids(calib_grid)
    calib_controller.set_calib_data(calib_files)
    calib_controller.create_masks(threshold)
    calib_controller.save()
    calib_controller.save_masks()

    calib_path = bugtracker.core.cache.calib_filepath(manager.metadata, manager.grid_info)
    assert os.path.isfile(calib_path)
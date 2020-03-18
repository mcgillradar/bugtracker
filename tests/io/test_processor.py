import os
import datetime

import pytest

import bugtracker


def test_generic_processor():

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    with pytest.raises(TypeError):
        test_processor = bugtracker.io.processor.Processor(metadata, grid_info)


def test_iris_init():

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    iris_processor = bugtracker.io.processor.IrisProcessor(metadata, grid_info)


def test_iris_empty_data():
    """
    The IrisProcessor should raise a ValueError if you ask it
    to process an empty list.
    """

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    empty_list = []

    processor = bugtracker.io.processor.IrisProcessor(metadata, grid_info)

    with pytest.raises(ValueError):
        processor.process_sets(empty_list)


def test_iris_actual_data():
    """
    Verifying processing of test data.
    """

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    config = bugtracker.config.load("./bugtracker.json")
    sample_iris = bugtracker.core.samples.iris_set_xam(config)
    sample_list = [sample_iris]

    processor = bugtracker.io.processor.IrisProcessor(metadata, grid_info)
    processor.process_sets(sample_list)

    output_dir = os.path.join(config['netcdf_dir'], metadata.radar_id)
    output_file = os.path.join(output_dir, 'dbz_201307171949.nc')
    assert os.path.isfile(output_file)


def test_nexrad_actual_data():

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    template_date = "201907190300"
    sample_date = "201907190300"
    fmt = "%Y%m%d%H%M"

    template_dt = datetime.datetime.strptime(template_date, fmt)
    sample_dt = datetime.datetime.strptime(sample_date, fmt)

    radar_id = "kcbw"
    manager = bugtracker.io.nexrad.NexradManager(config, radar_id)
    manager.populate(template_dt)

    nexrad_file = manager.get_closest(sample_dt)

    processor = bugtracker.io.processor.NexradProcessor(manager)
    processor.process_file(nexrad_file)

    output_dir = os.path.join(config['netcdf_dir'], manager.metadata.radar_id)
    output_file = os.path.join(output_dir, "dbz_201907190259.nc")
    assert os.path.isfile(output_file)



def test_odim_actual_data():

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    template_date = "202002190300"
    sample_date = "202002191630"
    fmt = "%Y%m%d%H%M"

    template_dt = datetime.datetime.strptime(template_date, fmt)
    sample_dt = datetime.datetime.strptime(sample_date, fmt)

    radar_id = "casbv"
    manager = bugtracker.io.odim.OdimManager(config, radar_id)
    manager.populate(template_dt)

    odim_file = manager.get_closest(sample_dt)

    processor = bugtracker.io.processor.OdimProcessor(manager)
    processor.process_file(odim_file)

    output_dir = os.path.join(config['netcdf_dir'], manager.metadata.radar_id)
    output_file = os.path.join(output_dir, "dbz_202002191630.nc")
    assert os.path.isfile(output_file)

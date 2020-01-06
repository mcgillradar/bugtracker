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


def test_not_implemented():
    """
    Confirm via unit test that OdimProcessor and NexradProcessor have
    not been implemented.
    """

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    with pytest.raises(NotImplementedError):
        odim = bugtracker.io.processor.OdimProcessor(metadata, grid_info)

    with pytest.raises(NotImplementedError):
        nexrad = bugtracker.io.processor.NexradProcessor(metadata, grid_info)


def test_iris_empty_data():
    """
    The IrisProcessor should raise a ValueError if you ask it
    to process an empty list.
    """

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    empty_list = []

    processor = bugtracker.io.processor.IrisProcessor(metadata, grid_info)
    processor.init_plotter()

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
    processor.init_plotter()
    processor.process_sets(sample_list)

    output_file = os.path.join(config['netcdf_dir'], 'dbz_201307171949.nc')
    assert os.path.isfile(output_file)


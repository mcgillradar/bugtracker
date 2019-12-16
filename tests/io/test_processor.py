import pytest

import bugtracker


def test_generic_processor():

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    with pytest.raises(TypeError):
        test_processor = bugtracker.io.processor.Processor(metadata, grid_info)


def test_iris_processor_init():

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
import os

import numpy as np

import bugtracker


def test_iris_output():

    config = bugtracker.config.load("../apps/bugtracker.json")

    grid_info = bugtracker.core.samples.grid_info()
    metadata = bugtracker.core.samples.metadata()

    iris_set_xam = bugtracker.core.samples.iris_set_xam(config)
    iris_data = bugtracker.core.iris.IrisData(iris_set_xam)

    iris_data.dbz_filtered = np.random.rand(6,720,512)
    iris_data.dbz_unfiltered = np.random.rand(6,720,512)
    iris_data.joint_product = np.random.rand(720,512)

    iris_data.dbz_elevs = np.linspace(-0.5, 0.5, num=6)
    iris_data.dop_elevs = [-0.5, -0.2, -0.5]

    iris_data.velocity = np.random.rand(3,720,512)
    iris_data.spectrum_width = np.random.rand(3,720,512)
    iris_data.total_power = np.random.rand(3,720,512)

    iris_output = bugtracker.io.models.IrisOutput(metadata, grid_info)
    iris_output.populate(iris_data)
    iris_output.validate()

    output_filename = "test_netcdf_output.nc"
    iris_output.write(output_filename)

    assert os.path.isfile(output_filename)
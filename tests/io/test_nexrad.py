import os
import datetime

import bugtracker


def test_nexrad_manager():

    config_path = "../apps/bugtracker.json"
    config = bugtracker.config.load(config_path)

    test_radar = "kcbw"
    test_date = datetime.datetime(2019, 7, 19)
    test_date_data = datetime.datetime(2019, 7, 19, 6)

    manager = bugtracker.io.nexrad.NexradManager(config, test_radar)
    manager.populate(test_date)

    data_file = manager.get_closest(test_date_data)
    sample_nex = manager.extract_data(data_file)

    dbz_shape = sample_nex.dbz_unfiltered.shape

    assert dbz_shape[1] == 720
    assert dbz_shape[2] == 1832

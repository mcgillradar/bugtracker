

import numpy as np

import bugtracker


def test():

    # How about a sampling of iris data to test out the filter?

    test_filter = bugtracker.core.filter.Filter()
    #geo_filter = bugtracker.calib.geometry.GeometryFilter(None, None, None)
    elev_filter = bugtracker.calib.clutter.ClutterFilter()
    precip_filter = bugtracker.core.precip.PrecipFilter()

    print(type(test_filter))
    #print(type(geo_filter))
    print(type(elev_filter))
    print(type(precip_filter))

    print("test_prop:", elev_filter.test_prop)



def main():

    metadata = bugtracker.core.samples.metadata()
    grid_info = bugtracker.core.samples.grid_info()

    # should be a sample_convol() and sample_dopvol()
    angles = np.linspace(-0.5, 3.0, num=7)
    dbz_sample = np.zeros((7,720,512), dtype=float)

    clutter_filter = bugtracker.calib.clutter.ClutterFilter(metadata, grid_info)
    clutter_filter.setup(angles)

    clutter_filter.breakdown()
    clutter_filter.filter_3d[0,:,:].fill(True)
    clutter_filter.breakdown()
    clutter_filter.test_method()


main()
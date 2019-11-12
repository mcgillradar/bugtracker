"""
Currently unused processor class
"""

import numpy as np

import bugtracker


class Processor:

    def __init__(self):

        self.grid_info = bugtracker.core.grid.GridInfo(1000, 360, 125.0, 0.5)
        azims = self.grid_info.azims
        gates = self.grid_info.gates
        dims = (azims, gates)
        self.data = np.zeros(dims, dtype=float)


    def filter(self):
        pass

    def output_netcdf(self):
        pass


class IrisProcessor(Processor):

    def __init__(self):

        super().__init__()


class OdimProcessor(Processor):
    """
    Processor for Odim H5 files (new Environment Canada format)
    """

    def __init__(self):

        super().__init__()


class NexradProcessor(Processor):
    """
    Processor for US Weather Service NEXRAD file format
    """

    def __init__(self):

        super().__init__()
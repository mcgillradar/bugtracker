"""
This file is part of Bugtracker
Copyright (C) 2019  McGill Radar Group

Bugtracker is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Bugtracker is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Bugtracker.  If not, see <https://www.gnu.org/licenses/>.
"""

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
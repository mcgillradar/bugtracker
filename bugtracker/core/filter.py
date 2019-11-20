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
This program currently has 3 types of filters:
1) Geometry filter
2) Clutter filter
3) Precipitation filter

(1) and (2) are determined during the calibration, and 
(3) depends on each scan.

However, the common link is that these filters generate a boolean 
mask on a 3D array of scans. In the case of IRIS, DOPVOL and
CONVOL can be invoked separately.

Keep in mind that the filtering occors on dbz data.

3 file formats:

1) IRIS
2) ODIM_H5
3) NEXRAD
"""

import abc
import numpy as np


class Filter(abc.ABC):

    def __init__(self, metadata, grid_info):
        
        self.metadata = metadata
        self.grid_info = grid_info

        self.filter_3d = None
        self.vertical_angles = None


    def get_dims(self):
        return self.filter_3d.shape

    def check_dims(self):
        """
        Making sure dimensions correspond
        """

        angles = len(self.vertical_angles)
        azims = self.grid_info.azims
        gates = self.grid_info.gates

        if (angles, azims, gates) != self.filter_3d.shape:
            raise ValueError(f"Invalid dimensions: {self.filter_3d.shape}")

    def level_coverage(self, level):
        """
        Gets the percent coverage for a certain level
        Returns float between 0 and 1
        """

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        level_cells = azims * gates
        hits = self.filter_3d[level,:,:].sum()

        return hits / level_cells

    def coverage(self):
        """
        Gets the total (all-elevation) coverage.
        Returns the mask percentage.
        """

        angles = len(self.vertical_angles)
        azims = self.grid_info.azims
        gates = self.grid_info.gates
        hits = self.filter_3d.sum()
        cells = angles * azims * gates

        return hits / cells

    def breakdown(self):
        """
        Print a level-by-level breakdown of the filter coverage.
        """

        print("Filter coverage breakdown:")
        num_levels = len(self.vertical_angles)

        for x in range(0, num_levels):
            cov = self.level_coverage(x)
            elev_angle = self.vertical_angles[x]
            print(f"Elev angle: {elev_angle}, coverage: {cov}")


    def set_filter(self, fill_entry=True):
        
        # 3D filter can be initialized as all True
        # or all False values.
        if not isinstance(fill_entry, bool):
            raise ValueError("Fill must be boolean type.")

        angles = len(self.vertical_angles)
        azims = self.grid_info.azims
        gates = self.grid_info.gates

        dims_3d = (angles, azims, gates)
        self.filter_3d = np.zeros(dims_3d, dtype=bool)
        self.filter_3d.fill(fill_entry)

    def setup(self, angles):

        self.vertical_angles = angles
        self.set_filter(fill_entry=False)



"""
Bugtracker - A radar utility for tracking insects
Copyright (C) 2020 Frederic Fabry, Daniel Hogg

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Here we use the 4/3 earth radius model of atmospheric propagation
to model beam propagation.
"""

import numpy as np

from bugtracker.core.filter import Filter


class GeometryFilter(Filter):

    def __init__(self, metadata, grid_info, elevation):

        super().__init__(metadata, grid_info)

        self.elevation = elevation

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        self.dims = (azims, gates)

        # making sure grid dimensions align
        bugtracker.core.utils.check_size(elevation, grid_info)


    def mask_trajectory(self, beam_heights):
        """
        Eelvation is taken from self.elevation
        """

        level_mask = np.zeros(self.dims, dtype=bool)

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        for azim in azims:
            for gate in gates:
                if beam_heights[azims, gates] > self.elevation[azims, gates]:
                    level_mask[azims, gates] = True
                else:
                    pass

        return level_mask


    def get_beam_heights(self):
        """
        Testing
        """

        return np.zeros(self.dims, dtype=float)


    def get_mask(self, beam_angle):
        """
        Get mask for one level.
        Completely independent of input radar data and based
        solely on geometry.
        """

        # essentially linspace
        azim_bins = self.grid_info.azim_bins()
        gate_bins = self.grid_info.gate_bins()

        # Assuming that numpy mask is just a boolean array
        # where False means the value is masked out

        beam_heights = self.get_beam_heights()
        level_mask = self.mask_trajectory(beam_heights)

        return level_mask
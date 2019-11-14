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

from bugtracker.core.filter import Filter


class PrecipFilter(Filter):

    def __init__(self, metadata, grid_info):
        super().__init__(metadata, grid_info)


    def verify_dims(self):
        
        if self.dbz_3d is None:
            raise ValueError("dbz_3d not set")

        if self.filter_3d is None:
            raise ValueError("filter_3d not set")

        dbz_shape = self.dbz_3d.shape
        filter_shape = self.dbz_3d.shape

        if len(dbz_shape) != 3 or len(filter_shape) != 3:
            raise ValueError("3D array expected.")

        if dbz_shape != filter_shape:
            raise ValueError(f"Incompatible numpy arrays: {dbz_shape}, {filter_shape}")

        num_angles = dbz_shape[0]
        num_azims = dbz_shape[1]
        num_gates = dbz_shape[2]

        if num_angles != len(self.vertical_angles):
            raise ValueError()

        if num_azims != self.grid_info.azims:
            raise ValueError(f"Incompatible azims: {azims}, {self.grid_info.azims}")


    def set_dbz(self):
        # Set dbz array
        pass
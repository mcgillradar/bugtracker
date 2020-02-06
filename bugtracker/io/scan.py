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

import abc

import bugtracker.config


class ScanData(abc.ABC):
    """
    This is a base class which IrisData, NexradData all inherit
    """

    def __init__(self, metadata, grid_info, scan_datetime):

        self.config = bugtracker.config.load("./bugtracker.json")
        self.metadata = metadata
        self.grid_info = grid_info
        self.datetime = scan_datetime
        self.validate_scan()


    def validate_scan(self):

        if self.config is None:
            raise ValueError("Configuration cannot be None")

        if self.metadata is None:
            raise ValueError("metadata cannot be None")

        if self.grid_info is None:
            raise ValueError("grid_info cannot be None")

        if self.datetime is None:
            raise ValueError("Scan must have a valid datetime")
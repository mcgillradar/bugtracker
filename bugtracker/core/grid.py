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

import datetime

import numpy as np

import pyart


class GridInfo():

    def __init__(self, gates, azims, gate_step, azim_step, azim_offset=0.0, gate_offset=0.0):

        # Azims are in degrees, and gate units are in meters.

        self.gates = gates
        self.azims = azims
        self.gate_step = gate_step
        self.azim_step = azim_step
        self.gate_offset = gate_offset
        self.azim_offset = azim_offset


    def __str__(self):
        rep = "GridInfo:\n"

        rep += f"gates: {self.gates}\n"
        rep += f"azims: {self.azims}\n"
        rep += f"gate_step: {self.gate_step} m\n"
        rep += f"azim_step: {self.azim_step} deg\n"
        rep += f"gate_offset: {self.gate_offset} m\n"
        rep += f"azim_offset: {self.azim_offset} deg\n"

        return rep


    def get_range(self):

        # Missing some fields with info
        _range = dict()
        begin = 0
        end = (self.gates - 1) * self.gate_step
        _range['data'] = np.linspace(begin, end, self.gates)
        return _range

    def get_azim_dict(self):

        # Missing some fields with info
        azim_dict = dict()
        begin = 0
        end = (self.azims - 1) * self.azim_step
        azim_dict['data'] = np.linspace(begin, end, self.azims)
        return azim_dict


    def get_elev_dict(self):

        # Missing some fields with info
        elev_dict = dict()
        elev_dict['data'] = np.zeros(self.azims, dtype=float)
        return elev_dict


    def get_fixed_angle(self):

        # Missing some fields with info
        fixed_angle = dict()
        fixed_angle['data'] = np.zeros(1, dtype=float)
        return fixed_angle


    def get_time(self, scan_dt):

        time_dict = dict()
        timestamp = scan_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        units_str = f"seconds since {timestamp}"
        time_dict['units'] = units_str
        time_dict['standard_name'] = 'time'
        time_dict['long_name'] = 'time_in_seconds_since_volume_start'
        time_dict['calendar'] = 'gregorian'
        time_dict['comment'] = 'Coordinate variable for time. Time at the center of each ray, in fractional seconds since the global variable time_coverage_start'
        time_dict['data'] = np.zeros(self.azims, dtype=float)
        return time_dict


    def get_sweep_number(self):
        sweep_number = dict()
        sweep_number['units'] = 'count'
        sweep_number['standard_name'] = 'sweep_number'
        sweep_number['long_name'] = 'Sweep number'
        sweep_number['data'] = np.zeros(1, dtype=int)
        return sweep_number


    def get_dbz_field(self, dbz_array):

        dbz_dict = dict()
        dbz_dict['units'] = 'dBZ'
        dbz_dict['standard_name'] = 'equivalent_reflectivity_factor'
        dbz_dict['long_name'] = 'Total power'
        dbz_dict['coordinates'] = 'elevation azimuth range'
        dbz_dims = (self.azims, self.gates)
        dbz_dict['data'] = np.zeros(dbz_dims, dtype=float)
        dbz_dict['data'] = dbz_array[:,:]
        return dbz_dict


    def get_latitude(self, latitude):

        lat = dict()
        lat['long_name'] = 'Latitude'
        lat['standard_name'] = 'Latitude'
        lat['units'] = 'degrees_north'
        lat['data'] = np.zeros(1, dtype=float)
        lat['data'][0] = latitude
        return lat


    def get_longitude(self, longitude):

        lon = dict()
        lon['long_name'] = 'Longitude'
        lon['standard_name'] = 'Longitude'
        lon['units'] = 'degrees_east'
        lon['data'] = np.zeros(1, dtype=float)
        lon['data'][0] = longitude
        return lon


    def check_dbz_dims(self, dbz_array):
        
        dbz_shape = dbz_array.shape

        if dbz_shape[0] != self.azims:
            raise ValueError("Invalid azims:", dbz_shape[0])

        if dbz_shape[1] != self.gates:
            raise ValueError("Invalid gates:", dbz_shape[1])


    def get_start_indices(self):

        start_idx = dict()
        start_idx['long_name'] = 'Index of first ray in sweep, 0-based'
        start_idx['units'] = 'count'
        start_idx['data'] = np.zeros(1, dtype=int)
        start_idx['data'][0] = 0
        return start_idx


    def get_end_indices(self):

        end_idx = dict()
        end_idx['long_name'] = 'Index of last ray in sweep, 0-based'
        end_idx['units'] = 'count'
        end_idx['data'] = np.zeros(1, dtype=int)
        end_idx['data'][0] = self.azims - 1
        return end_idx


    def create_radar(self, dbz_array, metadata):
        
        self.check_dbz_dims(dbz_array)

        # Create new 'radar' object from scratch, 
        
        time_dict = self.get_time(metadata.scan_dt)
        _range = self.get_range()
        fields = dict()
        fields['dbz'] = self.get_dbz_field(dbz_array)
        pyart_metadata = dict()
        scan_type = "ppi"

        print(metadata)
        print(metadata.lat)
        print(metadata.lon)

        latitude = self.get_latitude(metadata.lat)
        longitude = self.get_longitude(metadata.lon)
        altitude = dict()
        sweep_number = self.get_sweep_number()
        sweep_mode = dict()
        fixed_angle = self.get_fixed_angle()
        sweep_start_ray_index = self.get_start_indices()
        sweep_end_ray_index = self.get_end_indices()
        azimuth = self.get_azim_dict()
        elevation = self.get_elev_dict()

        radar = pyart.core.radar.Radar(time_dict, _range, fields, pyart_metadata, scan_type, latitude, longitude, altitude,
                                       sweep_number, sweep_mode, fixed_angle, sweep_start_ray_index,
                                       sweep_end_ray_index, azimuth, elevation)

        return radar
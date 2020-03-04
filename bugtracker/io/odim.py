"""
This file is part of Bugtracker
Copyright (C) 2020  McGill Radar Group

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

import os
import glob
import datetime
import math
import time

import numpy as np
import pyart
from scipy import interpolate

import bugtracker.core.utils
from bugtracker.io.scan import ScanData


class OdimManager:

    """
    The OdimManager class is responsible for getting 
    """

    def __init__(self, config, radar_id):

        self.config = config
        self.radar_id = radar_id.lower()
        self.odim_dir = self.config['input_dirs']['odim']

        self.metadata = None
        self.grid_info = None


    def datetime_from_file(self, filepath):
        """
        Extracting the timestamp with the file (with validation)
        """

        basename = os.path.basename(filepath)
        components = basename.split("_")
        if len(components) < 2:
            raise ValueError("Cannot split filename into components.")

        datestamp = components[0] + components[1]

        fmt = "%Y%m%d%H%M"

        file_dt = datetime.datetime.strptime(datestamp, fmt)

        return file_dt


    def get_closest(self, target_dt):
        """
        Get the closest radar scan to the specified date,
        and return an error if the closest is more than 30mins away
        or if no input files are found.

        Check +/- 1 hour range
        """

        start = target_dt + datetime.timedelta(hours=-1)
        end = target_dt + datetime.timedelta(hours=1)

        files_in_range = self.get_range(start, end)

        if len(files_in_range) == 0:
            raise FileNotFoundError("No files found within +/- 1 hour range of target datetime")

        min_diff = 999999999
        min_idx = -1

        for x in range(0, len(files_in_range)):
            current_file = files_in_range[x]
            file_dt = self.datetime_from_file(current_file)
            diff = file_dt - target_dt
            total_seconds = abs(diff.total_seconds())
            if total_seconds < min_diff:
                min_diff = total_seconds
                min_idx = x

        closest = files_in_range[min_idx]

        if not os.path.isfile(closest):
            raise FileNotFoundError(closest)

        return closest


    def get_range(self, start, end):
        """
        Return all ODIM_H5 radar files within the specified
        date range.
        """

        radar_lower = self.radar_id.lower()
        radar_upper = self.radar_id.upper()
        glob_string = f"*{radar_lower}.h5"
        search = os.path.join(self.odim_dir, radar_lower, glob_string)
        all_files = glob.glob(search)
        all_files.sort()

        range_list = []

        for input_file in all_files:
            current_dt = self.datetime_from_file(input_file)
            if start <= current_dt and current_dt <= end:
                range_list.append(input_file)

        for file in range_list:
            if not os.path.isfile(file):
                raise FileNotFoundError(f"File does not exist: {file}")

        return range_list



    def extract_metadata(self, odim_file):
        """
        Extracting metadata object from ODIM_H5 file
        """

        odim_handle = pyart.aux_io.read_odim_h5(odim_file)

        radar_name = odim_handle.metadata['instrument_name']

        radar_id = self.radar_id

        latitude = odim_handle.latitude['data'][0]
        longitude = odim_handle.longitude['data'][0]

        abs_lat = abs(latitude)
        abs_lon = abs(longitude)

        if abs_lat > 180.0:
            raise ValueError(f"Invalid latitude: {latitude}")

        if abs_lon > 360.0:
            raise ValueError(f"Invalid longitude: {longitude}")

        datestamp = odim_handle.time['units'].split(' ')[-1]
        scan_dt = datetime.datetime.strptime(datestamp, "%Y-%m-%dT%H:%M:%SZ")

        metadata = bugtracker.core.metadata.Metadata(radar_id, scan_dt, latitude, longitude, radar_name)
        return metadata


    def extract_grid(self, odim_file):

        odim_handle = pyart.aux_io.read_odim_h5(odim_file)

        reflectivity_shape = odim_handle.fields['reflectivity']['data'].shape

        # TODO: Placeholder values
        gates = reflectivity_shape[1]
        azims = 720

        azim_step = 0.5
        azim_offset = 0.25

        gate_step = odim_handle.range['meters_between_gates']
        gate_offset = odim_handle.range['meters_to_center_of_first_gate']

        grid_info = bugtracker.core.grid.GridInfo(gates, azims, gate_step, azim_step,
                                                  azim_offset=azim_offset, gate_offset=gate_offset)

        return grid_info



    def populate(self, template_date):

        template_file = self.get_closest(template_date)

        if not os.path.isfile(template_file):
            raise FileNotFoundError(template_file)

        self.metadata = self.extract_metadata(template_file)
        self.grid_info = self.extract_grid(template_file)


    def extract_data(self, odim_file):

        if self.metadata is None:
            raise ValueError("metadata cannot be None")

        if self.grid_info is None:
            raise ValueError("grid_info cannot be None")

        t0 = time.time()

        odim_data = OdimData(odim_file, self.metadata, self.grid_info)
        
        t1 = time.time()
        elapsed = t1 - t0
        print(f"Time for data extraction: {elapsed:.3f} s")
        return odim_data


class OdimData(ScanData):

    """
    Data wrapper for OdimH5
    """

    def __init__(self, odim_file, metadata, grid_info):

        scan_dt = metadata.scan_dt

        super().__init__(metadata, grid_info, datetime)

        if not os.path.isfile(odim_file):
            raise FileNotFoundError("Odim file does not exist")

        self.handle = pyart.aux_io.read_odim_h5(odim_file)
        field_shape = self.handle.fields['reflectivity']['data'].shape
        print("Field shape:", field_shape)

        self.azims_per_lower = 720
        self.azims_per_upper = 360

        self.dbz_unfiltered = self.init_field()
        self.velocity = self.init_field()
        self.cross_correlation_ratio = self.init_field()
        self.diff_reflectivity = self.init_field()

        self.check_consistency()

        input_dims = self.handle.fields['reflectivity']['data'].shape

        num_lower_levels = self.get_num_lower()
        num_upper_levels = self.get_num_upper()

        self.dbz_elevs = self.get_scan_angles(num_lower_levels, num_upper_levels)

        if len(self.dbz_elevs) != self.dbz_unfiltered.shape[0]:
            raise ValueError(f"Inconsistent number of scan angles: {len(self.dbz_elevs)} != {self.dbz_unfiltered.shape[0]}")

        self.check_levels(num_lower_levels, num_upper_levels, input_dims)

        self.fill_lower(num_lower_levels, num_upper_levels)
        self.fill_upper(num_upper_levels)

        # This is not a "classification filter", but a preprocessing step
        min_dbz_cutoff = self.config['odim_settings']['dbz_cutoff']
        print("Min dbz cutoff:", min_dbz_cutoff)
        print(type(min_dbz_cutoff))

        print(type(self.dbz_unfiltered))
        bugtracker.core.utils.arr_info(self.dbz_unfiltered, "unfiltered")
        bugtracker.core.utils.arr_info(self.cross_correlation_ratio, "ratio")
        #self.dbz_unfiltered = np.ma.masked_where(np.isnan(self.dbz_unfiltered), self.dbz_unfiltered)
        self.dbz_unfiltered = np.ma.masked_where(self.dbz_unfiltered < min_dbz_cutoff, self.dbz_unfiltered)



    def __str__(self):

        rep = "OdimData:\n"

        rep += f"Dimensions: {self.reflectivity.shape}"

        return rep


    def get_num_lower(self):

        """
        Assumed to be a constant for ODIM sweeps.
        """

        return 6


    def get_num_upper(self):

        """
        For now, I think we can pick only the lower scans.
        I can include the upper ones, but what is the purpose
        of including them if they are out of the plane for
        bugs?

        For performance considerations I am settings these to
        zero for now.
        """

        """
        fixed_angles = self.handle.fixed_angle['data']

        num_total_angles = len(fixed_angles)
        upper_angles = num_total_angles - self.get_num_lower()

        print("Upper angles:", upper_angles)

        return upper_angles
        """

        return 0


    def init_field(self):

        num_lower_levels = self.get_num_lower()
        num_upper_levels = self.get_num_upper()

        num_vertical = num_lower_levels + num_upper_levels

        field_shape = (num_vertical,self.grid_info.azims, self.grid_info.gates)
        field = np.zeros(field_shape, dtype=np.float32)

        print("field shape:", field_shape)

        return field


    def get_scan_angles(self, num_lower_levels, num_upper_levels):

        fixed_angle = self.handle.fixed_angle['data']
        angle_list = list(fixed_angle)

        # We want the angles to go from smallest to largest
        # as a convention.
        angle_list.reverse()
        print("ODIM angle list:", angle_list)

        # Selecting only lower scans

        return angle_list[0:self.get_num_lower()]


    def check_field_dims(self, field_name):

        if field_name not in self.handle.fields:
            raise KeyError(f"Missing field {field_name}")

        # Can't reliably check azims, because they are 
        # bundled into the vertical direction.

        field_dims = self.handle.fields[field_name]['data'].shape

        if len(field_dims) != 2:
            raise ValueError(f"Invalid field_dims: {field_dims}")

        if self.grid_info.gates != field_dims[1]:
            raise ValueError("Invalid gate number")


    def check_consistency(self):
        
        template_msg = "\nYou may need to call the method 'build_template()' from the NexradManager"

        # Check that all data grids initialized

        if self.metadata is None:
            raise ValueError(f"metadata not initialized {template_msg}")

        if self.grid_info is None:
            raise ValueError(f"product_grid not initialized {template_msg}")

        # check field dimensions

        self.check_field_dims("reflectivity")
        self.check_field_dims("velocity")
        self.check_field_dims("cross_correlation_ratio")
        self.check_field_dims("differential_reflectivity")


    def check_levels(self, num_lower, num_upper, input_shape):
        """
        A consistency check to make sure the num_lower/num_upper
        detection worked correctly.
        """

        if len(input_shape) != 2:
            raise ValueError("Error: 2-dimensional array expected.")


    def fill_lower_field(self, field, field_key, start_idx, elev_idx):
        
        print("elev_idx:", elev_idx)

        end_idx = start_idx + self.azims_per_lower

        active_section = self.handle.fields[field_key]['data'][start_idx:end_idx,:]

        if active_section.shape[0] != field.shape[1]:
            raise ValueError("Incompatible azims")
        if active_section.shape[1] != field.shape[2]:
            raise ValueError("Incompatible gates")

        field[elev_idx,:,:] = active_section[:,:]


    def fill_lower_scan(self, start_idx, elev_idx):

        self.fill_lower_field(self.dbz_unfiltered, "reflectivity", start_idx, elev_idx)
        self.fill_lower_field(self.cross_correlation_ratio, "cross_correlation_ratio", start_idx, elev_idx)
        self.fill_lower_field(self.velocity, "velocity", start_idx, elev_idx)
        self.fill_lower_field(self.diff_reflectivity, "differential_reflectivity", start_idx, elev_idx)


    def fill_lower(self, num_lower, num_upper):

        print("Filling lower fields")

        upper_block = self.azims_per_upper * num_upper

        for x in range(0, num_lower):
            start_idx = upper_block + self.azims_per_lower * x
            elev_idx = len(self.dbz_elevs) - (1 + x + num_upper)
            current_angle = self.dbz_elevs[elev_idx]
            self.fill_lower_scan(start_idx, elev_idx)



    def fill_upper_field(self, field, field_key, start_idx, elev_idx):

        print("Elev idx:", elev_idx)

        azims = self.azims_per_upper

        for x_start in range(0, azims):
            # Some modular arithmatic for wraparound
            x_end = (x_start + 1) % azims
            output_start = 2 * x_start
            output_mid = output_start + 1

            field_start = start_idx + x_start
            field_end = start_idx + x_end

            field_start_ray = self.handle.fields[field_key]['data'][field_start,:]
            field_end_ray = self.handle.fields[field_key]['data'][field_end,:]

            # Setting start first, no data manipulation required11
            field[elev_idx,output_start,:] = field_end_ray[:]

            # Setting midpoint, must average two arrays
            field[elev_idx,output_mid,:] = (field_start_ray[:] + field_end_ray[:]) / 2.0


    def fill_upper_scan(self, start_idx, elev_idx):

        self.fill_upper_field(self.dbz_unfiltered, "reflectivity", start_idx, elev_idx)
        self.fill_upper_field(self.cross_correlation_ratio, "cross_correlation_ratio", start_idx, elev_idx)
        self.fill_upper_field(self.velocity, "velocity", start_idx, elev_idx)
        self.fill_upper_field(self.diff_reflectivity, "differential_reflectivity", start_idx, elev_idx)



    def fill_upper(self, num_upper):

        print("Filling upper fields")

        for x in range(0, num_upper):
            start_idx = self.azims_per_upper * x
            elev_idx = len(self.dbz_elevs) - (1 + x)
            current_angle = self.dbz_elevs[elev_idx]
            print("start_idx:", start_idx)
            print("current_angle:", current_angle)
            self.fill_upper_scan(start_idx, elev_idx)
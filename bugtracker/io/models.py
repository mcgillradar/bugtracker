"""
This file contains the data models for exporting
netCDF4 content
"""

import abc
import numpy as np
import netCDF4 as nc


class BaseOutput(abc.ABC):

    def __init__(self, metadata, grid_info, radar_filetype):

        self.metadata = metadata
        self.grid_info = grid_info
        self.radar_filetype = radar_filetype

        self.dbz_3d = np.zeros((1,1,1), dtype=float)


    def write_metadata(self, handle):
        """
        Put in all of the important attributes.
        """

        # For the record, I am very confused about these two different
        # ways of serializing metadata in netCDF4. I used the first
        # one below to set some global attributes for the calibration.

        # What is the difference? Will need to run some tests

        dset.setncattr_string("calib_start", timestamp)
        dset.setncattr("calib_hours", calib_hours)

        # Adding metadata
        dset.latitude = metadata.lat
        dset.longitude = metadata.lon
        dset.radar_id = metadata.radar_id
        dset.datetime = metadata.scan_dt.strftime("%Y%m%d%H%M")
        dset.name = metadata.name

        # Specific metadata for radar_filetype


    def write(self, filename):

        dset = nc.open(filename, mode="w")

        # fill in here

        nc.close()

    def validate(self):

        if self.dbz_3d is None:
            raise ValueError("Main dbz array cannot be null")

        # check dimensions


class IrisOutput(BaseOutput):
    """
    Test
    """

    def __init__(self, metadata, grid_info):

        super().__init__(metadata, grid_info, "iris")

        self.velocity = None
        self.spectrum_width = None

        self.dbz_angles = self.get_dbz_angles()
        self.dop_angles = self.get_doppler_angles()


    def set_velocity(self, velocity_3d):

        self.velocity = velocity_3d



    def set_spectrum_width(self, spectrum_width_3d):

        self.spectrum_width = spectrum_width_3d


    def get_dbz_angles(self):
        """
        Take the join of all angles, unique only, order.
        """

        all_angles = self.dbz_angles + self.dop_angles
        angle_set = set(all_angles)
        angle_list = list(angle_set)
        angle_list.sort()

        return angle_list


    def get_doppler_angles(self):
        """
        Take only unique doppler angles
        """

        doppler_set = set(self.dop_angles)
        doppler_list = list(doppler_set)
        doppler_list.sort()

        return doppler_list


    def validate():

        super().validate()

        valid = True

        # check dimensions also


    def write():
        """
        Appends. File is created in super class.

        Imporant to ensure file is not corrupted before
        saving to netCDF4. If you are doing batch processing
        of netCDF4, you may want to include a try/except block
        to handle ValueError.
        """

        self.validate()

        super().write()

        nc.open(filename, mode="a")

        # fill in here

        nc.close()


class OdimOutput(BaseOutput):

    def __init__(self, metadata, grid_info):

        raise NotImplementedError("OdimOutput")


class NexradOutput(BaseOutput):

    def __init__(self, metadata, grid_info):

        raise NotImplementedError("NEXRAD")
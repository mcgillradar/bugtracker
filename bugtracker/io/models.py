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
import numpy as np
import netCDF4 as nc

import bugtracker.config

class BaseOutput(abc.ABC):

    def __init__(self, metadata, grid_info, radar_filetype):

        self.config = bugtracker.config.load("./bugtracker.json")
        self.metadata = metadata
        self.grid_info = grid_info
        self.radar_filetype = radar_filetype


    def write_metadata(self, dset):
        """
        Put in all of the important attributes and metadata
        using the dset file handle.
        """

        dset.latitude = self.metadata.lat
        dset.longitude = self.metadata.lon
        dset.radar_id = self.metadata.radar_id
        dset.datetime = self.metadata.scan_dt.strftime("%Y%m%d%H%M")
        dset.name = self.metadata.name
        dset.filetype = self.radar_filetype


    def write(self, filename):

        dset = nc.Dataset(filename, mode="w")

        self.write_metadata(dset)
        # Create dbz_elevs, azims, gates as dimensions

        azims = self.grid_info.azims
        gates = self.grid_info.gates
        dbz_elevs = self.dbz_elevs
        num_dbz_elevs = len(dbz_elevs)

        dset.createDimension("dbz_elevs", num_dbz_elevs)
        dset.createDimension("azims", azims)
        dset.createDimension("gates", gates)

        nc_dbz_elevs = dset.createVariable("dbz_elevs", np.float32, ('dbz_elevs',))
        nc_dbz_filtered = dset.createVariable("dbz_filtered", np.float32, ('dbz_elevs','azims','gates'))
        nc_dbz_unfiltered = dset.createVariable("dbz_unfiltered", np.float32, ('dbz_elevs','azims','gates'))
        nc_dbz_joint = dset.createVariable("dbz_joint", np.float32, ('azims','gates'))

        nc_dbz_elevs[:] = dbz_elevs[:]
        nc_dbz_filtered[:,:,:] = self.dbz_filtered[:,:,:]
        nc_dbz_unfiltered[:,:,:] = self.dbz_unfiltered[:,:,:]
        nc_dbz_joint = self.joint_product[:,:]

        dset.close()


    def validate(self):

        if self.dbz_filtered is None:
            raise ValueError("dbz_filtered array cannot be null.")

        if self.dbz_unfiltered is None:
            raise ValueError("dbz_unfiltered array cannot be null.")

        if self.dbz_filtered.shape != self.dbz_unfiltered.shape:
            raise ValueError("dbz grids must have the same dimension.")

        if self.dbz_elevs is None:
            raise ValueError("No scan angles")

        # check dimensions
        azims = self.grid_info.azims
        gates = self.grid_info.gates

        dbz_azims = self.dbz_filtered.shape[1]
        dbz_gates = self.dbz_filtered.shape[2]

        if dbz_azims != azims:
            raise ValueError(f"Incompatible azims: {dbz_azims} != {azims}")

        if dbz_gates != gates:
            raise ValueError(f"Incompatible gates: {dbz_gates} != {gates}")

        if self.joint_product is None:
            raise ValueError("joint_product cannot be null.")

        joint = self.joint_product.shape

        if len(joint) != 2:
            raise ValueError("joint_product must be a 2D array.")

        if azims != joint[0] or gates != joint[1]:
            raise ValueError(f"Incompatible dims for joint_product: {joint[0]},{joint[1]}")


    def append_target_id(self, filename, id_matrix):
        """
        Appends. File is created in super class.

        Imporant to ensure file is not corrupted before
        saving to netCDF4. If you are doing batch processing
        of netCDF4, you may want to include a try/except block
        to handle ValueError.
        """

        self.validate()

        dset = nc.Dataset(filename, mode="a")

        nc_target_id = dset.createVariable("target_id", int, ('dbz_elevs','azims','gates'))

        nc_target_id[:,:,:] = id_matrix[:,:,:]

        dset.close()


class IrisOutput(BaseOutput):
    """
    Test
    """

    def __init__(self, metadata, grid_info):

        super().__init__(metadata, grid_info, "iris")

        self.velocity = None
        self.spectrum_width = None
        self.total_power = None


    def populate(self, iris_data):

        self.dbz_filtered = iris_data.dbz_filtered
        self.dbz_unfiltered = iris_data.dbz_unfiltered
        self.joint_product = iris_data.joint_product
        self.dbz_elevs = iris_data.dbz_elevs

        self.dop_elevs = iris_data.dopvol_elevs
        self.velocity = iris_data.velocity
        self.spectrum_width = iris_data.spectrum_width
        self.total_power = iris_data.total_power


    def validate(self):

        super().validate()

        # check dimensions also
        velocity_shape = self.velocity.shape
        spectrum_shape = self.spectrum_width.shape
        power_shape = self.total_power.shape

        if velocity_shape != spectrum_shape:
            raise ValueError(f"Incompatible shapes {velocity_shape} != {spectrum_shape}")

        if velocity_shape != power_shape:
            raise ValueError(f"Incompatible shapes {velocity_shape} != {spectrum_shape}")


    def write(self, filename):
        """
        Appends. File is created in super class.

        Imporant to ensure file is not corrupted before
        saving to netCDF4. If you are doing batch processing
        of netCDF4, you may want to include a try/except block
        to handle ValueError.
        """

        self.validate()

        super().write(filename)

        dset = nc.Dataset(filename, mode="a")

        dop_elevs = self.dop_elevs
        num_dop_elevs = len(dop_elevs)
        dop_dims = ('dop_elevs', 'azims', 'gates')

        dset.createDimension("dop_elevs", num_dop_elevs)

        nc_dop_elevs = dset.createVariable("dop_elevs", np.float32, ('dop_elevs',))
        nc_power = dset.createVariable("total_power", np.float32, dop_dims)
        nc_velocity = dset.createVariable("velocity", np.float32, dop_dims)
        nc_spectrum = dset.createVariable("spectrum_width", np.float32, dop_dims)

        nc_dop_elevs[:] = dop_elevs[:]
        nc_power[:,:,:] = self.total_power[:,:,:]
        nc_velocity[:,:,:] = self.velocity[:,:,:]
        nc_spectrum[:,:,:] = self.spectrum_width[:,:,:]

        dset.close()


class OdimOutput(BaseOutput):

    def __init__(self, metadata, grid_info):

        raise NotImplementedError("OdimOutput")


class NexradOutput(BaseOutput):

    def __init__(self, metadata, grid_info):

        super().__init__(metadata, grid_info, "nexrad")


    def populate(self, nexrad_data):
        """
        TODO: Keep filtered separate
        """

        output_shape = nexrad_data.dbz_unfiltered.shape
        flattened_shape = (self.grid_info.azims, self.grid_info.gates)

        # A key part of keeping the output files a reasonable size
        # is to only keep lowest N scans for the output. We keep
        # all scans during the processing for the precip filter.

        max_scans = self.config['nexrad_settings']['vertical_scans']

        self.dbz_filtered = nexrad_data.dbz_filtered[0:max_scans,:,:]
        self.dbz_unfiltered = nexrad_data.dbz_unfiltered[0:max_scans,:,:]
        self.joint_product = nexrad_data.joint_product[:,:]
        self.dbz_elevs = nexrad_data.dbz_elevs[0:max_scans]

        self.spectrum_width = nexrad_data.spectrum_width[0:max_scans,:,:]
        self.velocity = nexrad_data.velocity[0:max_scans,:,:]
        self.cross_correlation_ratio = nexrad_data.cross_correlation_ratio[0:max_scans,:,:]


    def validate(self):

        super().validate()

        pass


    def write(self, filename):
        """
        Appends. File is created in super class.

        Imporant to ensure file is not corrupted before
        saving to netCDF4. If you are doing batch processing
        of netCDF4, you may want to include a try/except block
        to handle ValueError.
        """

        self.validate()

        super().write(filename)

        dset = nc.Dataset(filename, mode="a")

        #self.spectrum_width = nexrad_data.spectrum_width
        #self.velocity = nexrad_data.velocity
        #self.cross_corrleation_ratio = nexrad_data.cross_correlation_ratio

        nc_spectrum = dset.createVariable("spectrum_width", np.float32, ('dbz_elevs','azims','gates'))
        nc_velocity = dset.createVariable("velocity", np.float32, ('dbz_elevs','azims','gates'))
        nc_ratio = dset.createVariable("cross_correlation_ratio", np.float32, ('dbz_elevs','azims','gates'))

        nc_spectrum[:,:,:] = self.spectrum_width[:,:,:]
        nc_velocity[:,:,:] = self.velocity[:,:,:]
        nc_ratio[:,:,:] = self.cross_correlation_ratio[:,:,:]

        dset.close()
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

        self.dbz_3d = None


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

        nc_dbz_elevs = dset.createVariable("dbz_elevs", float, ('dbz_elevs',))
        nc_dbz_3d = dset.createVariable("dbz", float, ('dbz_elevs','azims','gates'))

        nc_dbz_elevs[:] = dbz_elevs[:]
        nc_dbz_3d[:,:,:] = self.dbz_3d[:,:,:]

        dset.close()


    def validate(self):

        if self.dbz_3d is None:
            raise ValueError("Main dbz array cannot be null")

        # check dimensions
        azims = self.grid_info.azims
        gates = self.grid_info.gates

        dbz_azims = self.dbz_3d.shape[1]
        dbz_gates = self.dbz_3d.shape[2]

        if dbz_azims != azims:
            raise ValueError(f"Incompatible azims: {dbz_azims} != {azims}")

        if dbz_gates != gates:
            raise ValueError(f"Incompatible gates: {dbz_gates} != {gates}")


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

        self.dbz_3d = np.zeros((6,720,512), dtype=float)

        self.dbz_elevs = np.linspace(1, 6, num=6)
        self.dop_elevs = iris_data.dopvol_elevs()

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

        nc_dop_elevs = dset.createVariable("dop_elevs", float, ('dop_elevs',))
        nc_power = dset.createVariable("total_power", float, dop_dims)
        nc_velocity = dset.createVariable("velocity", float, dop_dims)
        nc_spectrum = dset.createVariable("spectrum_width", float, dop_dims)

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

        raise NotImplementedError("NEXRAD")
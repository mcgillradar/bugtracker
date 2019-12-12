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


    def write_metadata(self, handle):
        """
        Put in all of the important attributes.
        """

        # For the record, I am very confused about these two different
        # ways of serializing metadata in netCDF4. I used the first
        # one below to set some global attributes for the calibration.

        # What is the difference? Will need to run some tests


        # Adding metadata
        dset.latitude = metadata.lat
        dset.longitude = metadata.lon
        dset.radar_id = metadata.radar_id
        dset.datetime = metadata.scan_dt.strftime("%Y%m%d%H%M")
        dset.name = metadata.name
        dset.filetype = self.radar_filetype


    def write(self, filename):

        dset = nc.open(filename, mode="w")

        # Create dbz_elevs, azims, gates as dimensions

        azims = self.grid_info.azims
        gates = self.grid_info.gates


        dset.createDimension("azims", azims)
        dset.createDimension("gates", gates)

        nc_lat = dset.createVariable("lats", float, ('azims','gates'))
        nc_lon = dset.createVariable("lons", float, ('azims', 'gates'))
        nc_altitude = dset.createVariable("altitude", float, ('azims', 'gates'))

        nc_lat[:,:] = self.lats[:,:]
        nc_lon[:,:] = self.lons[:,:]
        nc_altitude[:,:] = self.altitude[:,:]

        # For now, not saving masks

        dset.close()

        nc.close()

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

        self.velocity = iris_data.velocity
        self.spectrum_width = iris_data.spectrum_width
        self.total_power = iris_data.total_power


    def validate():

        super().validate()

        # check dimensions also
        velocity_shape = self.velocity.shape
        spectrum_shape = self.spectrum_width.shape
        power_shape = self.total_power.shape

        if velocity_shape != spectrum_shape:
            raise ValueError(f"Incompatible shapes {velocity_shape} != {spectrum_shape}")

        if velocity_shape != power_shape:
            raise ValueError(f"Incompatible shapes {velocity_shape} != {spectrum_shape}")


    def write(filename):
        """
        Appends. File is created in super class.

        Imporant to ensure file is not corrupted before
        saving to netCDF4. If you are doing batch processing
        of netCDF4, you may want to include a try/except block
        to handle ValueError.
        """

        self.validate()

        super().write(filename)

        nc.open(filename, mode="a")

        # fill in here

        nc.close()


class OdimOutput(BaseOutput):

    def __init__(self, metadata, grid_info):

        raise NotImplementedError("OdimOutput")


class NexradOutput(BaseOutput):

    def __init__(self, metadata, grid_info):

        raise NotImplementedError("NEXRAD")
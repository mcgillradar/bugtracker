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
Currently unused processor class
"""
import os
import abc
import datetime

import numpy as np
import netCDF4 as nc

import bugtracker
from bugtracker.core.precip import PrecipFilter

class Processor(abc.ABC):

    def __init__(self, metadata, grid_info):

        self.config = bugtracker.config.load("./bugtracker.json")

        self.metadata = metadata
        self.grid_info = grid_info
        self.calib_file = bugtracker.core.cache.calib_filepath(metadata, grid_info)
        self.plotter = None

        if not os.path.isfile(self.calib_file):
            raise FileNotFoundError("Missing calib file")

        self.load_universal_calib()
        self.verify_universal_calib()


    def load_universal_calib(self):
        """
        Load parts of the calibration file that are universal
        to all data types (i.e. lats, lons, altitude)
        """
        
        calib_file = self.calib_file

        dset = nc.Dataset(calib_file, mode='r')

        self.lats = dset.variables['lats'][:,:]
        self.lons = dset.variables['lons'][:,:]
        self.altitude = dset.variables['altitude'][:,:]

        dset.close()

    def verify_universal_calib(self):
        """
        Make sure all the dimensions are correct
        """

        polar_dims = (self.grid_info.azims, self.grid_info.gates)

        if self.lats.shape != polar_dims:
            raise ValueError(f"Lat grid invalid dims: {self.lats.shape}")
        
        if self.lons.shape != polar_dims:
            raise ValueError(f"Lon grid invalid dims: {self.lons.shape}")

        if self.altitude.shape != polar_dims:
            raise ValueError(f"Altitude grid invalid dims: {self.altitude.shape}")


    def init_plotter(self):
        """
        Activate the RadialPlotter. This code may need to be significantly
        modified if we need to do parallel plotting (multi-cpu to speed up
        the plotting of a large set of files).
        """

        radar_id = self.metadata.radar_id
        plot_dir = self.config['plot_dir']
        output_folder = os.path.join(plot_dir, radar_id)

        if not os.path.isdir(plot_dir):
            FileNotFoundError(f"This folder should have been created {plot_dir}")

        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)

        self.plotter = bugtracker.plots.radial.RadialPlotter(self.lats, self.lons, output_folder)

    @abc.abstractmethod
    def load_specific_calib(self):
        """
        Load parts of calib file that are specific to a particular
        filetype.
        """
        pass

    @abc.abstractmethod
    def verify_specific_calib(self):
        """
        Verify the dimensions are correct for filetype specific
        parts of the calibration
        """
        pass


class IrisProcessor(Processor):

    def __init__(self, metadata, grid_info):
        super().__init__(metadata, grid_info)
        self.load_specific_calib()
        self.verify_specific_calib()

    def load_specific_calib(self):
        """
        Iris-specific calibration data includes CONVOL/DOPVOL
        """

        calib_file = self.calib_file
        dset = nc.Dataset(calib_file, mode='r')

        self.convol_angles = dset.variables['convol_angles'][:]
        self.dopvol_angles = dset.variables['dopvol_angles'][:]
        self.convol_clutter = dset.variables['convol_clutter'][:,:,:]
        self.dopvol_clutter = dset.variables['dopvol_clutter'][:,:,:]

        dset.close()

    def verify_specific_calib(self):
        
        num_convol = len(self.convol_angles)
        num_dopvol = len(self.dopvol_angles)

        if num_convol <= 1:
            raise ValueError("Not enough CONVOL angles in calib")

        if num_dopvol <= 1:
            raise ValueError("Not enough DOPVOL angles in calib")

        azims = self.grid_info.azims
        gates = self.grid_info.gates

        convol_dim = (num_convol, azims, gates)
        dopvol_dim = (num_dopvol, azims, gates)

        if self.convol_clutter.shape != convol_dim:
            raise ValueError(f"Invalid convol dimensions: {self.convol_clutter.shape}")

        if self.dopvol_clutter.shape != dopvol_dim:
            raise ValueError(f"Invalid dopvol dimensions: {self.dopvol_clutter.shape}")


    def plot_graph(self, prefix, plot_type, angle, slice_data, plot_dt):

        label = f"{prefix}_{plot_type}_{angle}"
        max_range = 150

        self.plotter.set_data(slice_data, label, plot_dt, self.metadata, max_range)
        self.plotter.save_plot(min_value=-10, max_value=40)


    def plot_iris(self, iris_data, label_prefix):
        """
        Plots a set of iris data
        """

        if self.plotter is None:
            raise ValueError("Plotter has not been initialized!")

        print("Plotting:", label_prefix)

        print("Plotting convol")
        for x in range(0, len(self.convol_angles)):
            angle = self.convol_angles[x]
            slice_data = iris_data.convol[x,:,:]
            self.plot_graph(label_prefix, "convol", angle, slice_data, iris_data.datetime)

        print("Plotting dopvol")
        for x in range(0, len(self.dopvol_angles)):
            angle = self.dopvol_angles[x]
            slice_data = iris_data.dopvol[x,:,:]
            self.plot_graph(label_prefix, "dopvol", angle, slice_data, iris_data.datetime)



    def impose_filter(self, iris_data, np_convol, np_dopvol):
        """
        Standin method for applying joint filters
        """

        raw_dopvol_shape = iris_data.dopvol.shape
        raw_convol_shape = iris_data.convol.shape

        raw_dopvol_mask = np.ma.getmask(iris_data.dopvol)
        raw_convol_mask = np.ma.getmask(iris_data.convol)

        dopvol_mask = np.ma.mask_or(np_dopvol, raw_dopvol_mask)
        convol_mask = np.ma.mask_or(np_convol, raw_convol_mask)

        iris_data.dopvol = np.ma.array(iris_data.dopvol, mask=dopvol_mask)
        iris_data.convol = np.ma.array(iris_data.convol, mask=convol_mask)

        filtered_dopvol_shape = iris_data.dopvol.shape
        filtered_convol_shape = iris_data.convol.shape

        if raw_dopvol_shape != filtered_dopvol_shape:
            raise ValueError("Error in DOPVOL array size")

        if raw_convol_shape != filtered_convol_shape:
            raise ValueError("Error in new CONVOL array size")


    def process_set(self, iris_set):

        iris_data = bugtracker.core.iris.IrisData(iris_set)
        iris_data.fill_grids()

        # plot the unmodified files
        #self.plot_iris(iris_data, "raw")
        
        # construct the PrecipFilter from iris_set
        convol_precip = PrecipFilter(self.metadata, self.grid_info, self.convol_angles)
        dopvol_precip = PrecipFilter(self.metadata, self.grid_info, self.dopvol_angles)

        # For now, we are just using the ClutterFilter
        # Eventually, we will want to create a JointFilter from all 3
        # Here we are just using boolean numpy arrays

        convol_joint = self.convol_clutter.astype(bool)
        dopvol_joint = self.dopvol_clutter.astype(bool)

        # modify the files based on filters
        self.impose_filter(iris_data, convol_joint, dopvol_joint)

        # plot modified files
        self.plot_iris(iris_data, "filtered")


    def process_sets(self, iris_sets):

        for iris_set in iris_sets:
            self.process_set(iris_set)


class OdimProcessor(Processor):
    """
    Processor for Odim H5 files (new Environment Canada format)
    """

    def __init__(self):

        super().__init__()
        raise NotImplmentedError("OdimProcessor")


class NexradProcessor(Processor):
    """
    Processor for US Weather Service NEXRAD file format
    """

    def __init__(self):

        super().__init__()
        raise NotImplmentedError("NexradProcessor")
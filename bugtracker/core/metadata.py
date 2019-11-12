"""
The metadata extracts a standardized list of metatdata outputs
from a variety of input formats.
"""

import os

import pyart


class Metadata:
    """
    This class is a metadata container for all important info
    relating to a radar scan.

    Note that many functions in this codebase assume 'radar_id'
    must be unique. For Environment Canada radars we use the 3
    letter radar code 'xam', etc.
    """

    def __init__(self, radar_id, scan_dt, lat, lon, radar_name):

        self.radar_id = radar_id
        self.scan_dt = scan_dt
        self.lat = lat
        self.lon = lon
        self.name = radar_name

        if radar_id is None or scan_dt is None or lat is None or lon is None:
            raise ValueError("Null values are invalid for radar metadata.")


    def __str__(self):
        return f"radar_id: {self.radar_id}\nscan_dt: {self.scan_dt}\nlatitude: {self.lat}\nlongitude: {self.lon}\n"


def from_iris_set(iris_set):
    """
    Takes an IrisSet object as an input, creates corresponding
    metadata.
    """

    scan_dt = iris_set.datetime
    radar_id = iris_set.radar_id

    convol_file = iris_set.convol
    if not os.path.isfile(convol_file):
        raise FileNotFoundError(convol_file)

    iris_convol = pyart.io.read_sigmet(convol_file)

    latitude = iris_convol.latitude['data'][0]
    longitude = iris_convol.longitude['data'][0]

    # Bounds checking for lat/lon might look strange, but
    # this is because sometimes (-180,180) is chosen for longitude
    # and other times (0,360) is selected.

    abs_lat = abs(latitude)
    abs_lon = abs(longitude)

    if abs_lat > 180.0:
        raise ValueError(f"Invalid latitude: {latitude}")

    if abs_lon > 360.0:
        raise ValueError(f"Invalid longitude: {longitude}")


    #TODO: Include check for bytes type first
    radar_name = iris_convol.metadata['instrument_name'].decode()

    iris_metadata = Metadata(radar_id, scan_dt, latitude, longitude, radar_name)
    return iris_metadata
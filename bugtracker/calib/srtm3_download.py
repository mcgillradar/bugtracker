"""
Rather than making the end user configure the SRTM3 dataset,
this client utility will automatically figure out which elevation
files are needed to cover the radar domain.

These files will be saved to a cache, and will only need to be
downloaded once.
"""


import os
import glob
import shutil
import requests
import zipfile
from requests.exceptions import ConnectionError

import bugtracker.config


def download_file(url, output_dir):
    """
    This function should be able to handle a file that
    doesn't exist.
    """

    local_filename = url.split('/')[-1]
    full_local = os.path.join(output_dir, local_filename)
    with requests.get(url, stream=True) as r:
        with open(full_local, 'wb') as f:
            shutil.copyfileobj(r.raw, f)


class Downloader():
    """
    This downloader currently only supports North America, but it
    would be straightforward to extend it to other datasets.
    """


    def __init__(self, active_keys):
        """
        Active keys are the grid cells that correspond to the current radar,
        written in the form 'N47W089'
        """
        self.src_url = "https://dds.cr.usgs.gov/srtm/version2_1/SRTM3/North_America/"
        self.keys = active_keys
        self.config = bugtracker.config.load('./bugtracker.json')
        self.missing = None
        root_cache = self.config['cache_dir']
        self.srtm3_dir = os.path.join(root_cache, 'elevation', 'srtm3')
        self.zipped_dir = os.path.join(root_cache, 'elevation', 'zipped')

        if not os.path.isdir(self.srtm3_dir):
            raise FileNotFoundError(self.srtm3_dir)

        if not os.path.isdir(self.zipped_dir):
            raise FileNotFoundError(self.zipped_dir)


    def get_url(self, key):
        basename = key + ".hgt.zip"
        return os.path.join(self.src_url, basename)


    def self_test(self):
        """
        Check connection with SRTM3 dataset.
        Status code 200 indicates successful connection.
        """
        code_ok = 200
        r = requests.head(self.src_url)
        print(r.status_code)
        if r.status_code == code_ok:
            print("Connection to server successful.")
        else:
            raise ConnectionError(self.src_url)


    def set_missing_cells(self):
        """
        Look at unzipped SRTM3 files, see which ones are required.
        """

        search = os.path.join(self.srtm3_dir, "*.hgt")
        current_files = glob.glob(search)
        current_files.sort()
        current_set = set()

        for file in current_files:
            current_set.add(os.path.basename(file))

        self.missing = []

        for key in self.keys:
            full_basename = key + '.hgt'
            if full_basename in current_set:
                print("File already downloaded:", key)
            else:
                self.missing.append(key)

        print("Missing files:", self.missing)


    def download(self):

        files_to_download = []
        for key in self.missing:
            file_url = self.get_url(key)
            print("Downloading:", key)
            download_file(file_url, self.zipped_dir)


    def extract(self):
        """
        Unzip all of the files that are missing.
        """

        for key in self.missing:
            zip_file = os.path.join(self.zipped_dir, key + ".hgt.zip")
            print("Extracting:", zip_file)
            z = zipfile.ZipFile(zip_file)
            z.extractall(self.srtm3_dir)



    def final_check(self):
        """
        Checks that all files have been downloaded successfully.
        """

        self.set_missing_cells()
        if len(self.missing) > 0:
            raise FileNotFoundError(f"Files not downloaded: {self.missing}")
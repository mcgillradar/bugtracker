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

import os
import glob
import time
import datetime
import subprocess
import argparse
from xml.etree import ElementTree
import multiprocessing as mp

import requests
from bs4 import BeautifulSoup, SoupStrainer
from  urllib.request import urlopen

import bugtracker.config
import bugtracker.io.nexrad
import bugtracker.core.utils

"""
NEXRAD uses an XML pipeline
"""

def download_file(url, local_filename):

    print("url:", url)
    response = urlopen(url)
    CHUNK = 128 * 1024
    f = open(local_filename, 'wb')

    while True:
        chunk = response.read(CHUNK)
        if not chunk:
            break
        f.write(chunk)

    f.close()


class NexradDownloader:

    def __init__(self, config, args):
        self.args = args
        self.config = config
        self.local_root = config['input_dirs']['nexrad']
        self.remote_root = "https://noaa-nexrad-level2.s3.amazonaws.com"
        self.radar = args.radar
        self.date_list = self.get_dates()
        self.file_list = []
        self.download_list = []


    def make_folders(self):
        
        fmt = "%Y%m%d"
        start = datetime.datetime.strptime(self.args.start, fmt)
        end = datetime.datetime.strptime(self.args.end, fmt)

        input_folders = bugtracker.core.utils.get_input_folders(self.config, "nexrad", self.radar, start, end)
        for folder in input_folders:
            if not os.path.isdir(folder):
                print(f"Making folder: {folder}")
                os.makedirs(folder)


    def get_dates(self):
        """
        Creates a list of datetime objects for each date in the
        range that we want to download.
        """

        fmt = "%Y%m%d"
        start = datetime.datetime.strptime(self.args.start, fmt)
        end = datetime.datetime.strptime(self.args.end, fmt)
        date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days + 1)]
        return date_generated

        
    def __str__(self):

        str_rep = "NexradDownloader:\n"

        str_rep += f"remote_url: {self.remote_root}"

        return str_rep


    def parse_tag(self, input_tag):

        try:
            tag = input_tag.split("}")[-1]
            return tag.lower()
        except ValueError:
            print("Error: skipping")


    def scrape_page(self, date):

        year = date.strftime("%Y")
        month = date.strftime("%m")
        day = date.strftime("%d")
        code = self.radar.upper()

        url = f"{self.remote_root}/?delimiter=%2F&prefix={year}%2F{month}%2F{day}%2F{code}%2F"

        links = []

        xml_request = requests.get(url)
        tree = ElementTree.fromstring(xml_request.content)
        all_descendents = list(tree.iter())
        
        for desc in all_descendents:
            tag = self.parse_tag(desc.tag)
            if tag == "key":
                link = desc.text
                link_split = link.split("_")
                if len(link_split) < 2 or link_split[-1].lower() == "mdm":
                    # we want to exclude MDM records
                    pass
                else:
                    links.append(link)

        return links


    def get_file_list(self):
        """
        Come up with list of all files that need to be downloaded
        """

        all_links = []

        for date in self.date_list:
            links = self.scrape_page(date)
            print(date.strftime("%Y-%m-%d"))
            print(f"Number of links {len(links)}")
            all_links.extend(links)

        all_links.sort()
        self.remote_files = all_links


    def get_local_filename(self, basename):

        radar_id = self.radar.strip().lower()
        file_dt = bugtracker.io.nexrad.datetime_from_file(basename, radar_id)
        base_folder = os.path.join(self.config['input_dirs']['nexrad'], radar_id)
        subdir_fmt = os.path.join("%Y", "%m", "%d")
        subdir = file_dt.strftime(subdir_fmt)
        date_folder = os.path.join(base_folder, subdir)

        local_filename = os.path.join(date_folder, basename)
        print("local filename:", local_filename)
        return local_filename


    def exclude_local(self):
        """
        Exclude files that have already been downloaded in order to
        save bandwidth.
        """

        self.file_list = []

        for remote_file in self.remote_files:
            base = os.path.basename(remote_file)
            local_filename = self.get_local_filename(base)
            # Note: Do not use os.path.join because this is a URL, not a local path.
            remote_full = self.remote_root + '/' + remote_file
            if os.path.isfile(local_filename):
                print(f"File already downloaded, skipping: {local_filename}")
            else:
                self.file_list.append(remote_full)


    def download(self):
        """
        Download all files on 
        """

        download_dir = os.path.join(self.local_root, self.radar)

        arg_list = []
        
        self.file_list.sort()

        for url in self.file_list:
            base_filename = os.path.basename(url)
            local_filename = self.get_local_filename(base_filename)
            arg_list.append((url, local_filename))

        num_cores = mp.cpu_count()
        pool_size = num_cores - 2
        # Don't make the pool smaller than 1!
        pool_size = max(pool_size, 1)
        print("Num cores:", num_cores)
        print("Pool size:", pool_size)

        t0 = time.time()

        self.pool = mp.Pool()
        self.pool.starmap(download_file, arg_list)
        self.pool.close()
        self.pool.join()

        t1 = time.time()

        elapsed = t1 - t0
        num_files = len(self.file_list)

        print(f"{num_files} downloaded in {elapsed:.3f} s")


def sample_urls():
    remote_url = "https://noaa-nexrad-level2.s3.amazonaws.com/2019/07/01/KCBW/KCBW20190701_000033_V06"
    remote_url2 = "https://noaa-nexrad-level2.s3.amazonaws.com/2019/07/01/KCBW/KCBW20190701_000053_V06"
    # The Maine dataset radar is KCBW


def nexrad():
    """
    AWS NEXRAD downloader
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("start", help="Data timestamp YYYYmmdd")
    parser.add_argument("end", help="Data timestamp YYYYmmdd")
    parser.add_argument("radar", help="4 letter radar code")
    args = parser.parse_args()
    args.radar = args.radar.lower()
    print(args)

    config = bugtracker.config.load("./bugtracker.json")

    download_dir = config['input_dirs']['nexrad']
    # Make radar directory if it doesn't exist
    radar_folder = os.path.join(download_dir, args.radar)

    if not os.path.isdir(radar_folder):
        print(f"Making directory: {radar_folder}")
        os.mkdir(radar_folder)

    downloader = NexradDownloader(config, args)
    print(downloader)

    downloader.make_folders()
    downloader.get_file_list()
    downloader.exclude_local()
    downloader.download()


if __name__ == "__main__":
    nexrad()

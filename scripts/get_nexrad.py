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

import os
import glob
import subprocess
import argparse
import requests



def get_file_list(full_remote):

    text_list = os.path.join(full_remote, "fileList.txt")
    response = requests.get(text_list)
    all_lines = response.text

    file_list = all_lines.split('\n')

    stripped_list = []
    for file_url in file_list:
        stripped_list.append(os.path.join(full_remote, file_url.strip()))

    return stripped_list


def nexrad():
    """
    Downloader script for NEXRAD data dumps.
    For some reason recursive 'wget' calls are rejected by
    their servers, so I wrote this instead.
    """


    parser = argparse.ArgumentParser()
    parser.add_argument("has_folder", help="HAS folder name")
    args = parser.parse_args()
    remote_url = "https://www1.ncdc.noaa.gov/pub/has"
    full_remote = os.path.join(remote_url, args.has_folder)
    download_dir = "/storage/spruce/nexrad_data"

    file_list = get_file_list(full_remote)
    num_files = len(file_list)

    print(f"There are {num_files} files to download.")

    for file in file_list:
        subprocess.call(f"wget {file} -P {download_dir}", shell=True)


nexrad()
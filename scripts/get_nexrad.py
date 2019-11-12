"""
McGill Radar Group 2019
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
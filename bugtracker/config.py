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
import json


def locate_path(base_path):

    backup_path = "../apps/bugtracker.json"

    if os.path.isfile(base_path):
        return base_path
    elif os.path.isfile(backup_path):
        return backup_path
    else:
        raise FileNotFoundError(base_path)


def load(base_path):
    """
    This function provides a simple way to call load a .json
    config file.

    One weakness of this approach is that the top-level scripts
    must be run from within the /apps folder.
    """

    config_path = locate_path(base_path)

    config_file = open(config_path, mode='r')
    config_json = json.load(config_file)
    config_file.close()

    return config_json
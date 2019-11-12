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


def load(config_path):
    """
    This function provides a simple way to call load a .json
    config file.

    One weakness of this approach is that the top-level scripts
    must be run from within the /apps folder.
    """

    if not os.path.isfile(config_path):
        raise FileNotFoundError(config_path)

    config_file = open(config_path, mode='r')
    config_json = json.load(config_file)
    config_file.close()

    return config_json
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
What types of things do we want to do with NEXRAD files?

Well, we want a way to extract nexrad files from a folder
"""


class NexradManager:
    """
    The sole responsabilities of the NexradManager class are
    to return filenames and get metadata/grid_info from files
    """


    def __init__(self, config, args):

        self.config = config
        self.args = args



    def extract_metadata(nexrad_file):

        metadata = bugtracker.core.metadata()



class NexradData:

    def __init__(self, nexrad_file, metadata, grid_info):
        
        """
        Should be some grid verification checks
        """
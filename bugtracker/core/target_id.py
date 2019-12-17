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


def get_code_dict():
    """
    We only want to define these number codes in
    one place, that way we keep consistent.
    """

    code_dict = dict()
    code_dict['none'] = 0
    code_dict['clutter'] = 1
    code_dict['rain'] = 2
    code_dict['bugs'] = 3

    return code_dict


def get_code(target_code):

    target_code = target_code.lower().strip()
    code_dict = get_code_dict()

    if target_code not in code_dict:
        raise ValueError(f"Invaid target_code {target_code}")
    else:
        return code_dict[target_code]


class TargetId():

    def __init__(self):
        pass

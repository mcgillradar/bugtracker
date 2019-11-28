"""
The utils module is a grab bag of a bunch of useful code
that didn't seem to fit anywhere else.
"""

import datetime

import pytest

import bugtracker


def test_daterange():

    now = datetime.datetime.utcnow()
    last_hour = now + datetime.timedelta(hours=-1)

    with pytest.raises(ValueError):
        bugtracker.core.utils.DateRange(None, now)

    with pytest.raises(ValueError):
        bugtracker.core.utils.DateRange(now, None)

    with pytest.raises(ValueError):
        bugtracker.core.utils.DateRange(now, last_hour)

    interval = bugtracker.core.utils.DateRange(last_hour, now)
    assert interval.start == last_hour
    assert interval.end == now

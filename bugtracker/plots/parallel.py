import time
import multiprocessing as mp

import matplotlib.pyplot as plt
import numpy as np

import bugtracker.config
import bugtracker.plots.radial
import bugtracker.plots.identify

"""
Multiprocessing optimization:
-----------------------------
Given that Matplotlib is single-threaded, I am making the
design choice to have each plot on a single thread, but many
plots will be created at the same time, to minimize runtime
and maximize CPU usage.
"""


def plot_worker(lats, lons, config, iris_data, plot_type):

    time.sleep(5)

    plot_type = plot_type.lower().strip()

    if plot_type == 'filtered':
        print(plot_type)
    elif plot_type == 'unfiltered':
        print(plot_type)
    elif plot_type == 'joint':
        print(plot_type)
    elif plot_type == 'target_id':
        print(plot_type)
    else:
        raise ValueError(f"Unrecognizable plot type: {plot_type}")


class ParallelPlotter:
    """
    multiprocessing.Pool based class that allows mupliple plots to
    happen at the same time.
    """

    def __init__(self, lats, lons, iris_data):

        config = bugtracker.config.load("./bugtracker.json")

        self.lats = lats
        self.lons = lons
        self.iris_data = iris_data

        ll = ['filtered', 'unfiltered', 'joint', 'joint']

        args = []

        for t in ll:
            arglist = (self.lats, self.lons, config, self.iris_data, t)
            args.append(arglist)



        self.pool = mp.Pool()
        print(f"num processes: {self.pool._processes}")

        t0 = time.time()

        self.pool.starmap(plot_worker, args)

        t1 = time.time()

        elapsed = t1 - t0
        print(f"Should be slightly above 5: {elapsed:.3f}")
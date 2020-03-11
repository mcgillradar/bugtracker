"""
A test file designed to experiment with the Python
multiprocessing module.

I was having some issues with Windows compatibility for
multiprocessing, in particular the 
"""

import os
import pickle
import time
import multiprocessing as mp


scaling = 10000000

def worker(n, dummy_argument):

    start_idx = n * scaling
    stop_idx = (n+1) * scaling

    cumulative = 0
    print(f"Worker {n}")

    for x in range(start_idx, stop_idx):
        cumulative += x

    return cumulative


class Multiprocessor():

    def __init__(self):
        print("Initializing pool")
        self.pool = mp.Pool()


    def start(self, arg_list):
        print("Starting multiprocessing")
        self.results = self.pool.starmap(worker, arg_list)
        print(self.results)


    def sum(self):

        total = 0
        for result in self.results:
            total += result

        return total


    def stop(self):
        print("Calling close command")
        self.pool.close()
        self.pool.join()


def main():

    t0 = time.time()
    processor = Multiprocessor()


    endpoint = 60

    arg_list = []
    for x in range(0, endpoint):
        arg_list.append((x, "dummy_arg"))

    print(arg_list)
    processor.start(arg_list)
    processor.stop()
    total = processor.sum()
    print("total:", total)

    t1 = time.time()
    elapsed = t1 - t0
    print(f"Time elapsed: {elapsed:.3f}")

main()
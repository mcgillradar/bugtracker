import numpy as np

class DataGrid:

    def __init__(self):
        print("Constructing DataGrid")
        self.data = np.zeros((360,1000), dtype=float)

    def __enter__(self):
        print("Entering context")
        print("ENTER self.data", self.data)


    def __exit__(self, t, value, traceback):
        print("Leaving context")
        print(f"type: {t}, value: {value}, traceback: {traceback}")
        print("EXIT self.data", self.data)

def main():

    with DataGrid() as d_grid:
        pass

    d = DataGrid()

    my_slice = slice(0,8)
    print(d.data[0,my_slice])

main()
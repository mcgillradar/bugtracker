import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import interpolate

def main():

    x = np.arange(-25, 25, 0.25)
    y = np.arange(-25, 25, 0.25)

    xx, yy = np.meshgrid(x, y)
    print(type(xx))
    print(type(yy))
    z = np.sin(xx, yy)
    print("z-shape")
    print(z.shape)
    f = interpolate.interp2d(x,y,z,'cubic')
    xnew = np.arange(-25, 25, 1e-2)
    ynew = np.arange(-25, 25, 1e-2)
    znew = f(xnew, ynew)
    plt.plot(x, z[0,:], 'ro-', xnew, znew[0,:], 'b-')
    plt.savefig("interpolate2.png")
    

main()
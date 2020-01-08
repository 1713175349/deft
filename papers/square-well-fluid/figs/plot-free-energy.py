#!/usr/bin/python2
from __future__ import division
import matplotlib, sys
if 'show' not in sys.argv:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rc('text', usetex=True)

plt.figure()

# input: ['data/homogeneous/ww%g-kT%g.dat' % (ww, kT) for ww in [1.3] for kT in range(1,11)]
ww = 1.3
for kT in np.arange(1.0, 11.0, 1.0):
    fname = 'data/homogeneous/ww%g-kT%g.dat' % (ww, kT)
    data = np.loadtxt(fname)
    plt.plot(data[:,0], data[:,2], label=r'$T=%g$' % kT)
    plt.plot(data[:,0], data[:,3], '--')
    plt.plot(data[:,0], data[:,4], ':')

plt.legend(loc='best')
#plt.xlim(0, 0.53)
plt.ylim(-20, 50)
plt.xlabel(r'$\eta$')
plt.ylabel(r'$A$')
plt.savefig('figs/free-energy-vs-eta.pdf')


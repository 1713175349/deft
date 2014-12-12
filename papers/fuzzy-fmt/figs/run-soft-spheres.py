#!/usr/bin/python2

from __future__ import division
from os import system
import os
from math import pi

figsdir = 'papers/fuzzy-fmt/figs/'

srun = lambda n_reduced, kT: 'srun --mem=10000 -J wca-%.4f-%.4f time nice -19 ' % (n_reduced, kT)

if os.getcwd()[:5] != '/home' or os.system('srun true') != 0:
    # We are definitely not running on the cluster
    srun = lambda n_reduced, kT: 'time nice -19 '

# always remember to build the executable before running it
system('scons -U')

def run_soft_sphere(reduced_density, temperature):
    nspheres = round(reduced_density*2**(-5.0/2.0)*30**3)
    outfilename = 'wca-%.4f-%.4f.out' % (reduced_density, temperature)
    #system("%s %s/soft-sphere.mkdat %g %g > %s 2>&1 &" %
    system("%s %s/radial-wca.mkdat %g %g > %s 2>&1 &" %
           (srun(reduced_density, temperature), figsdir, reduced_density, temperature, outfilename))
'''
for kT in [1.0, 0.1, 0.01, 0.001]:
    for n_reduced in [0.7, 0.8, 0.9]:
        run_soft_sphere(n_reduced, kT)
'''
run_soft_sphere(0.83890, 0.71)
run_soft_sphere(0.957,2.48)
run_soft_sphere(01.095, 2.48)
run_soft_sphere(.5844,1.235)

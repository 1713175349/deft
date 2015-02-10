from __future__ import division
from os import system
import os
from math import pi

figsdir = 'papers/fuzzy-fmt/figs/'
bindir = '.'
if os.path.isdir('figs'):
    figsdir = 'figs/'
    bindir = '../..'

# always remember to build the executable before running it
system('scons -U')

def run_homogeneous(n_reduced, temperature, pot = ""):
    nspheres = round(n_reduced*2**(-5.0/2.0)*30**3)
    #width = (nspheres/density)**(1.0/3) # to get density just right!
    filename = '%s/mc%s-%.4f-%.4f' % (figsdir, pot, n_reduced, temperature)
    system("srun --mem=60 -J soft-%.4f-%.4f time nice -19 %s/soft-monte-carlo %d 0.01 0.001 %s.dat periodxyz 30 kT %g potential '%s' > %s.out 2>&1 &" %
           (n_reduced, temperature, bindir, nspheres, filename, temperature, pot, filename))

def run_walls(n_reduced, nspheres, temperature):
    if nspheres == 0:
        nspheres = round(n_reduced*2**(-5.0/2.0)*30**2*32) # reasonable guess
    filename = '%s/mcwalls-%.4f-%.4f-%d' % (figsdir, n_reduced, temperature, nspheres)
    system("srun --mem=60 -J softwalls-%.4f-%.4f time nice -19 %s/soft-monte-carlo %d 0.01 0.001 %s.dat periodxy 30 wallz 30 kT %g > %s.out 2>&1 &" %
           (n_reduced, temperature, bindir, nspheres, filename, temperature, filename))

def run_test_particle(n_reduced, temperature, testp_sigma,testp_eps,pot = ""):
    nspheres = round(n_reduced*2**(-5.0/2.0)*30**3)
    #width = (nspheres/density)**(1.0/3) # to get density just right!
    filename = '%s/mc_testp_%s-%.4f-%.4f' % (figsdir, pot, n_reduced, temperature)
    system("srun --mem=60 -J soft-testp-%.4f-%.4f time nice -19 %s/soft-monte-carlo %d 0.01 0.001 %s.dat periodxyz 30 kT %g TestP %f testp_eps %f potential '%s'  > %s.out 2>&1 &" %
           (n_reduced, temperature, bindir, nspheres, filename, temperature, testp_sigma, testp_eps, pot, filename))


def run_FCC(n_reduced, temperature, pot = ""):
    nspheres = round(n_reduced*2**(-5.0/2.0)*30**3)
    length = (1372/((n_reduced)*(2**(-5.0/2.0))))**(1.0/3.0)
    #width = (nspheres/density)**(1.0/3) # to get density just right!
    filename = '%s/mc%s-%.4f-%.4f' % (figsdir, pot, n_reduced, temperature)
    system("srun --mem=60 -J soft-%.4f-%.4f time nice -19 %s/soft-monte-carlo %d 0.01 0.001 %s.dat periodxyz 30 kT %g potential '%s' fcc %.4f > %s.out 2>&1 &" %
           (n_reduced, temperature, bindir, nspheres, filename, temperature, pot, length,  filename))





#for reduced_density in [0.2, 0.5, 1.0, 1.5]:
#  for reduced_temp in [0.2, 0.5, 1.0]:
#      print 'hello %g %g' % (reduced_density, reduced_temp)
#      run_walls(reduced_density, 0, reduced_temp)


argon_sigma=3.405
argon_eps=119.8

run_FCC(.76,2.5,"wca") 
#run_FCC(.8,5,"wca")
#run_FCC(.73,.2,"wca")
#run_FCC(.7,.1,"wca")


#for reduced_density in [0.1,.2,.4,.6]:
#    for temp in [0.1,.5]:
#        run_homogeneous(reduced_density, temp, "wca")


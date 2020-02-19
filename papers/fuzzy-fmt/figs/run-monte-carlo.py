from __future__ import division
from os import system
import os
from math import pi
import numpy

figsdir = 'papers/fuzzy-fmt/figs/'
bindir = '.'

# always remember to build the executable before running it
system('fac soft-monte-carlo')

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

def run_soft_walls(n_reduced, nspheres, temperature, correction_factor=1):
    if nspheres == 0:
        nspheres = round(n_reduced*2**(-5.0/2.0)*30**2*32) # reasonable guess
        nspheres = round(nspheres*correction_factor)
    filename = '%s/mc-soft-wall-%.4f-%.4f-%d' % (figsdir, n_reduced, temperature, nspheres)
    system("rq run -J wcawalls-%.4f-%.4f %s/soft-monte-carlo %d 0.01 0.001 %s.dat periodxy 30 softwallz 1 kT %g" %
           (n_reduced, temperature, bindir, nspheres, filename, temperature))

def run_test_particle(n_reduced, temperature, testp_sigma,testp_eps,pot = ""):
    nspheres = round(n_reduced*2**(-5.0/2.0)*30**3)
    #width = (nspheres/density)**(1.0/3) # to get density just right!
    filename = '%s/mc_testp_%s-%.4f-%.4f' % (figsdir, pot, n_reduced, temperature)
    system("srun --mem=60 -J soft-testp-%.4f-%.4f time nice -19 %s/soft-monte-carlo %d 0.01 0.001 %s.dat periodxyz 30 kT %g TestP %f testp_eps %f potential '%s'  > %s.out 2>&1 &" %
           (n_reduced, temperature, bindir, nspheres, filename, temperature, testp_sigma, testp_eps, pot, filename))

def run_FCC(n_reduced, temperature, pot = ""):
    nspheres = 4*7**3
    n = n_reduced*(2.0**(-5.0/2.0))
    total_volume = nspheres/n
    length = total_volume**(1.0/3.0)
    filename = '%s/mcfcc-%.4f-%.4f' % (figsdir, n_reduced, temperature)
    system("srun --mem=60 -J softfcc-%.4f-%.4f time nice -19 %s/soft-monte-carlo %d 0.01 0.001 %s.dat kT %g potential '%s' fcc %.15g > %s.out 2>&1 &" %
           (n_reduced, temperature, bindir, nspheres, filename, temperature, pot, length,  filename))

def run_FCC_walls(n_reduced, temperature, tweak_density = 1, pot = "wca"):
    nspheres = 4*7**3
    n = n_reduced*(2.0**(-5.0/2.0))*tweak_density
    total_volume = nspheres/n
    length = total_volume**(1.0/3.0)
    filename = '%s/mcfcc-walls-%.4f-%.4f' % (figsdir, n_reduced, temperature)
    if tweak_density != 1:
        filename = filename + '-tweaked-%.10g' % tweak_density
    system("srun --mem=60 -J softfcc-%.4f-%.4f time nice -19 %s/soft-monte-carlo %d 0.01 0.001 %s.dat kT %g potential '%s' fcc-walls %.15g > %s.out 2>&1 &" %
           (n_reduced, temperature, bindir, nspheres, filename, temperature, pot, length,  filename))


#argon_sigma=3.405
#argon_eps=119.8

#run_homogeneous(.42,.42,"wca")
# run_test_particle(0.83890,0.71,argon_sigma,argon_eps,"wca")
# run_test_particle(0.957,2.48,argon_sigma,argon_eps,"wca")
# run_test_particle(0.957,1.235,argon_sigma,argon_eps,"wca")
# run_test_particle(0.5844,1.235,argon_sigma,argon_eps,"wca")
# run_test_particle(1.095,2.48,argon_sigma,argon_eps,"wca")
# run_test_particle(1.096,2.48,argon_sigma/5,argon_eps/5,"wca")


#run_FCC(0.5844,1.235,"wca")


# for reduced_density in [0.8, 1.0]:
#    for temp in [0.1,.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0]:
#        run_FCC(reduced_density, temp, "wca")

# run_FCC(0.9, 0.55, 'wca')
# run_FCC(0.9, 0.6, 'wca')
# run_FCC(0.9, 0.65, 'wca')
# run_FCC(0.9, 0.7, 'wca')

# run_FCC(1.0, 2.5, 'wca')
# run_FCC(1.0, 1.55, 'wca')
# run_FCC(1.0, 1.5, 'wca')
# run_FCC(1.0, 1.45, 'wca')
# run_FCC(0.8, 0.33, 'wca')
# run_FCC(0.8, 0.35, 'wca')
# run_FCC(0.8, 0.37, 'wca')

run_soft_walls(1.0, 0, 10.0, correction_factor = 1/1.1241239670565355/0.9556961399999997)
run_soft_walls(1.0, 0,  5.0, correction_factor = 1/1.1252180592369307/0.9475263199999999)
run_soft_walls(1.0, 0,  2.5, correction_factor = 1/1.1160919128447668/0.95585656)
# run_soft_walls(1.0, 0, 1.0)
# run_soft_walls(1.0, 0, 0.1)

run_soft_walls(0.6, 0, 10.0, correction_factor = 0.6/0.6830454082048744*0.6/0.5689411)
run_soft_walls(0.6, 0,  5.0, correction_factor = 0.6/0.6832733794311285*0.6/0.57097722)
run_soft_walls(0.6, 0,  2.5, correction_factor = 0.6/0.682760359319242*0.6/0.5671544599999999)
run_soft_walls(0.6, 0,  1.0, correction_factor = 0.6/0.6875152281586531*0.6/0.56183994)
# run_soft_walls(0.6, 0, 0.1)

# run_FCC_walls(0.6, 10.0, 0.95044, "wca")
# run_FCC_walls(0.6, 2.5, 0.9577, "wca")
# run_FCC_walls(0.6, 0.1, 0.9740, "wca")
#run_FCC(1.0, 1.0, "wca")
#run_FCC(1.0, 0.5, "wca")
#run_FCC(1.0, 2.5, "wca")
#run_FCC(1.0, 5.0, "wca")
#run_FCC(1.0, 10.0, "wca")
#run_FCC(1.5, 2.5, "wca")


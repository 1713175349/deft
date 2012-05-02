#!/usr/bin/python

# We need the following two lines in order for matplotlib to work
# without access to an X server.
import matplotlib
matplotlib.use('Agg')

import pylab, numpy, sys

if len(sys.argv) != 6:
    print("Usage:  " + sys.argv[0] + " mc-filename.dat wb-filename.dat wbt-filename.dat wb-m2.dat out-filename.pdf")
    exit(1)

mcdata = numpy.loadtxt(sys.argv[1])
dftdata = numpy.loadtxt(sys.argv[2])
wbtdata = numpy.loadtxt(sys.argv[3])
wbm2data = numpy.loadtxt(sys.argv[4])

dft_len = len(dftdata[:,0])
dft_dr = dftdata[2,0] - dftdata[1,0]

mcoffset = 13
pylab.plot(mcdata[:,0]+mcoffset,mcdata[:,1]*4*numpy.pi/3,"b-",label='MC $n$')
pylab.plot(dftdata[:,0],dftdata[:,1]*4*numpy.pi/3,"b--",label='DFT $n$')
pylab.plot(wbtdata[:,0],wbtdata[:,1]*4*numpy.pi/3,"m-.",label='WBT $n$')
pylab.plot(wbm2data[:,0],wbm2data[:,1]*4*numpy.pi/3,"c--",label='Mark II $n$')

n0 = dftdata[:,6]
nA = dftdata[:,8]
pylab.plot(dftdata[:,0],n0*4*numpy.pi/3,"c--",label="$n_0$")
pylab.plot(dftdata[:,0],nA*4*numpy.pi/3,"m-.",label="$n_A$")

nAmc = mcdata[:,11]
n0mc = mcdata[:,10]
pylab.plot(mcdata[:,0]+mcoffset,n0mc*4*numpy.pi/3,"c-",label="MC $n_0$")
pylab.plot(mcdata[:,0]+mcoffset,nAmc*4*numpy.pi/3,"m-",label="MC $n_A$")

pylab.xlabel("position")
pylab.ylabel("filling fraction")

pylab.legend(loc='lower left', ncol=2).get_frame().set_alpha(0.5)

pylab.twinx()

stop_here = int(dft_len - 1/dft_dr)
print stop_here
start_here = int(2.5/dft_dr)

off = 2
me = 30
#pylab.plot(mcdata[:,0],mcdata[:,2+2*off]/nAmc,"r-",label="MC $g_\sigma^A$")
pylab.plot(dftdata[start_here:stop_here,0],dftdata[start_here:stop_here,5],"ro--",markevery=me,label="$g_\sigma^A$ (White Bear)")
pylab.plot(wbm2data[start_here:stop_here,0],wbm2data[start_here:stop_here,5],"r+--",markevery=me,label="$g_\sigma^A$ (mark II)",
           markerfacecolor='none',markeredgecolor='red', markeredgewidth=1)
pylab.plot(dftdata[:,0],dftdata[:,7],"rx--",markevery=me,label="Gross",
           markerfacecolor='none',markeredgecolor='red', markeredgewidth=1)


#pylab.plot(mcdata[:,0],mcdata[:,3+2*off]/n0mc,"g-",label="MC $g_\sigma^S$")
pylab.plot(dftdata[start_here:stop_here,0],dftdata[start_here:stop_here,3],
           "g+--",markevery=me,label="$g_\sigma^S$ (White Bear)")
pylab.plot(wbm2data[start_here:stop_here,0],wbm2data[start_here:stop_here,3],"go--",markevery=me,label="$g_\sigma^S$ (mark II)",
           markerfacecolor='none',markeredgecolor='green', markeredgewidth=1)
pylab.plot(dftdata[:,0],dftdata[:,4],"gx--",markevery=me,label="Yu and Wu")

pylab.ylim(ymin=0)
pylab.xlim(xmax=10)
pylab.ylabel("$g_\sigma$")

pylab.legend(loc='upper left', ncol=2).get_frame().set_alpha(0.5)

pylab.savefig(sys.argv[5])

# div = len(dftdata[:,0])
# sep = dftdata[1,0] - dftdata[0,0]
# L = sep*div
# mid = int (div/2.0)
# midsec = int (div/2.0) - 20
# Nb = 0
# for i in dftdata[midsec:mid,0]
#   Ni = dftdata[i,0]*sep
#   Nb = Nb +Ni

# nb = Nb/(20*20*20*sep*sep*sep) 

# Ntot = 0
# for j in dftdata[:,0]:
#   nj = dftdata[j,0]*sep
#   Ntot = Ntot + nj

# Ntot = Ntot/(sep*div*sep*div)

# Nextra = Ntot - L*nb
#want to put in terms of per Area and also put the whole thing in th cpp file.  The abovefor j in dftdata[:,0] is 
#quesionable as to what that will go through


# N = 0
# Totvol = 0
# for i in dftdata[:,0]:
#   vol = 4*numpy.pi/3*dftdata[i+1,0]*dftdata[i+1,0]*dftdata[i+1,0] - 4*numpy.pi/3*dftdata[i,0]*dftdata[i,0]*dftdata[i,0]
#   N = N + dftdata[i,1]*vol
#   Totvol = Totvol +vol

# NperVol = N/Totvol

# #print("For " + sys.argv[2] + " total number per volume = %f. Multiply this by your total volume to get the same filling fraction.",(N/Totvol),)jj 

# strFile = "figs/FillingFracInfo.dat"
# file = open(strFile , "a")
# file.write("For " + sys.argv[2] + " total number per volume = " + str(NperVol) + ".\n")
# file.close()

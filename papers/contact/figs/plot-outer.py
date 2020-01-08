#!/usr/bin/python

# We need the following two lines in order for matplotlib to work
# without access to an X server.
import matplotlib
matplotlib.use('Agg')

import pylab, numpy, sys

if len(sys.argv) != 4:
    print(("Usage:  " + sys.argv[0] + " RADIUS <integer filling fraction in tenths> out-filename.pdf"))
    exit(1)

radiusname = sys.argv[1]
ffdigit = sys.argv[2]
pdffilename = sys.argv[3]
dftdatafilename = "figs/outer-sphereWB-%s-00.%s.dat" % (radiusname, ffdigit)
dftdata = numpy.loadtxt(dftdatafilename)
r = dftdata[:, 0]
n = dftdata[:, 1]
n0 = dftdata[:, 2]
nA = dftdata[:, 3]
gS = dftdata[:, 4]
gA = dftdata[:, 5]
gyuwu = dftdata[:, 6]
gross = dftdata[:, 7]

mcdatafilename = "figs/mc-outer-sphere-%s-0.%s.dat" % (radiusname, ffdigit)
mcdata = numpy.loadtxt(mcdatafilename)

mc_len = len(mcdata[:, 0])
dft_len = len(r)
dft_dr = r[2] - r[1]
padding = 4 # amount of extra space in cell
radius = round(r[dft_len-1]) - padding/2
showrmax = radius + 1
showrmin = radius - 6

mcdata = numpy.insert(mcdata, mc_len, 0, 0)
mcdata[mc_len, 0]=radius

nA_mc = mcdata[:, 11]
n0_mc = mcdata[:, 10]
n0_mc[mc_len]=1
r_mc = mcdata[:, 0]
n_mc = mcdata[:, 1]
off = 1
gA_mc = mcdata[:, 2+2*off] / nA_mc
gS_mc = mcdata[:, 3+2*off] / n0_mc

pylab.figure(figsize=(7, 6))
pylab.subplots_adjust(hspace=0.001)

n_plt = pylab.subplot(3, 1, 3)
n_plt.axvline(x=radius/2, color='k', linestyle=':')
n_plt.plot(r_mc/2, n_mc*4*numpy.pi/3, "b-", label='MC $n$')
n_plt.plot(r/2, n*4*numpy.pi/3, "b--", label='DFT $n$')
#n_plt.plot(r/2,n0*4*numpy.pi/3,"c-.",label="$n_0$")
#n_plt.plot(r/2,nA*4*numpy.pi/3,"m--",label="$n_A$")
#n_plt.plot(r/2,n0*4*numpy.pi/3,"c--",label="$n_0$")
#n_plt.plot(r/2,nA*4*numpy.pi/3,"m-.",label="$n_A$")
if (n[2]*4*numpy.pi/3 < 0.15 and n[2]*4*numpy.pi/3 > 0.05):
    n_plt.legend(loc='lower left', ncol=1).draw_frame(False) #get_frame().set_alpha(0.5)
else:
    n_plt.legend(loc='upper left', ncol=1).draw_frame(False) #get_frame().set_alpha(0.5)
n_plt.yaxis.set_major_locator(pylab.MaxNLocator(4, steps=[1, 5, 10], prune='upper'))
pylab.ylim(0, n.max()*4*numpy.pi/3*1.1)
pylab.xlim(showrmin/2, showrmax/2)
pylab.xlabel(r"$r$/$\sigma$")
pylab.ylabel("filling fraction")

#pylab.legend(loc='lower left', ncol=2).get_frame().set_alpha(0.5)

#pylab.twinx()

off = 2
me = 4
A_plt = pylab.subplot(3, 1, 1)
#A_plt.set_title("Spherical cavity with radius %s and filling fraction 0.%s" % (radiusname, ffdigit))
A_plt.axvline(x=radius/2, color='k', linestyle=':')
A_plt.plot(r_mc/2, gA_mc, "r-", label="$g_\sigma^A$ MC")
A_plt.plot(r[r>=showrmin]/2, gA[r>=showrmin], "ro--", markevery=me, label="$g_\sigma^A$ this work")
A_plt.plot(r/2, gross, "rx--", markevery=me, label="Gross",
           markerfacecolor='none', markeredgecolor='red', markeredgewidth=1)
A_plt.legend(loc='lower left', ncol=1).draw_frame(False) #get_frame().set_alpha(0.5)
A_plt.yaxis.set_major_locator(pylab.MaxNLocator(integer=True, prune='upper'))
pylab.xlim(showrmin/2, showrmax/2)
#matplotlib.ticks(arange(0.5, 1.5, 3.5))

sphere_end = int(dft_len - 1/dft_dr)

pylab.ylabel("$g^A$")

S_plt = pylab.subplot(3, 1, 2)
S_plt.axvline(x=radius/2, color='k', linestyle=':')
S_plt.plot(r_mc/2, gS_mc, "g-", label="$g_\sigma^S$ MC")
S_plt.plot(r[0:sphere_end]/2, gS[0:sphere_end], "go--", markevery=me, label="$g_\sigma^S$ this work")
S_plt.plot(r/2, gyuwu, "gx--", markevery=me, label="Yu and Wu")
if (n[2]*4*numpy.pi/3 < 0.15 and n[2]*4*numpy.pi/3 > 0.05):
    S_plt.legend(loc='lower left', ncol=1).draw_frame(False) #get_frame().set_alpha(0.5)
else:
    S_plt.legend(loc='upper left', ncol=2).draw_frame(False) #get_frame().set_alpha(0.5)
S_plt.yaxis.set_major_locator(pylab.MaxNLocator(integer=True, prune='upper'))
pylab.xlim(showrmin/2, showrmax/2)

pylab.ylabel("$g^S$")

xticklabels = A_plt.get_xticklabels() + S_plt.get_xticklabels()
pylab.setp(xticklabels, visible=False)

pylab.savefig(pdffilename)

pylab.show()

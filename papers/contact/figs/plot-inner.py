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
dftdatafilename = "figs/inner-sphereWB-%04.1f-0.%d0-mean.dat" % (2*float(radiusname), int(ffdigit))
print('Using', dftdatafilename)
dftdata = numpy.loadtxt(dftdatafilename)
r = dftdata[:, 0]
n = dftdata[:, 1]
n0 = dftdata[:, 2]
gS = dftdata[:, 3]
gyuwu = dftdata[:, 4]
nA = dftdata[:, 5]
gA = dftdata[:, 6]
gross = dftdata[:, 7]

dftdatafilename2 = "figs/inner-sphereWBm2-%04.1f-0.%d0-mean.dat" % (2*float(radiusname), int(ffdigit))
print('Using', dftdatafilename2)
dftdata2 = numpy.loadtxt(dftdatafilename2)
r_2 = dftdata2[:, 0]
n_2 = dftdata2[:, 1]
n0_2 = dftdata2[:, 2]
gS_2 = dftdata2[:, 3]
gyuwu_2 = dftdata2[:, 4]
nA_2 = dftdata2[:, 5]
gA_2 = dftdata2[:, 6]
gross_2 = dftdata2[:, 7]

mcdatafilename = "figs/mc-inner-sphere-%s-0.%s.dat" % (radiusname, ffdigit)
print('Using', mcdatafilename)
mcdata = numpy.loadtxt(mcdatafilename)
nA_mc = mcdata[:, 11]
n0_mc = mcdata[:, 10]
r_mc = mcdata[:, 0]
n_mc = mcdata[:, 1]
off = 2 # 2 is large and 3 is huge
gA_mc = mcdata[:, 2+2*off] / nA_mc
gS_mc = mcdata[:, 3+2*off] / n0_mc

dft_len = len(r)
dft_dr = r[2] - r[1]
padding = 4 # amount of extra space in cell
radius = float(radiusname)
showrmax = radius + 6
showrmin = max(radius - 1, 0)

pylab.figure(figsize=(7, 6))
pylab.subplots_adjust(hspace=0.001)

n_plt = pylab.subplot(3, 1, 3)
n_plt.axvline(x=radius/2, color='k', linestyle=':')
n_plt.plot(r_mc/2, n_mc*4*numpy.pi/3, "b-", label='MC $n$')
n_plt.plot(r[r>=radius]/2, n[r>=radius]*4*numpy.pi/3, "b--", label='DFT $n$')
#n_plt.plot(r/2,n0*4*numpy.pi/3,"c-.",label="$n_0$")
#n_plt.plot(r/2,nA*4*numpy.pi/3,"m--",label="$n_A$")
#n_plt.plot(r_2[r_2>=radius],n_2[r_2>=radius]*4*numpy.pi/3,"b--",label='DFT $n$ (mark II)')
#n_plt.plot(r,n0*4*numpy.pi/3,"c--",label="$n_0$")
#n_plt.plot(r,nA*4*numpy.pi/3,"m-.",label="$n_A$")
if (n[dft_len-3]*4*numpy.pi/3 < 0.15 and n[dft_len-3]*4*numpy.pi/3 > 0.05):
    n_plt.legend(loc='lower right', ncol=1).draw_frame(False)  #get_frame().set_alpha(0.5)
else:
    n_plt.legend(loc='upper right', ncol=1).draw_frame(False) #get_frame().set_alpha(0.5)
n_plt.yaxis.set_major_locator(pylab.MaxNLocator(3, steps=[1, 5, 10], prune='upper'))
pylab.xlim(showrmin/2, showrmax/2)
pylab.ylim(0, n.max()*4*numpy.pi/3*1.1)
pylab.xlabel(r"$r$/$\sigma$")
pylab.ylabel("filling fraction")

#pylab.legend(loc='lower left', ncol=2).get_frame().set_alpha(0.5)

#pylab.twinx()

off = 2
me = 4
A_plt = pylab.subplot(3, 1, 1)
#A_plt.set_title("Spherical solute with radius %s and filling fraction 0.%s" % (radiusname, ffdigit))
A_plt.axvline(x=radius/2, color='k', linestyle=':')
A_plt.plot(r_mc/2, gA_mc, "r-", label="$r_\sigma^A$ MC")
A_plt.plot(r[r>=showrmin]/2, gA[r>=showrmin], "ro--", markevery=me, label="$g_\sigma^A$ this work")
#A_plt.plot(r_2[r_2>=showrmin],gA_2[r_2>=showrmin],"r.--",markevery=me,label="$g_\sigma^A$ (White Bear mark II)")
A_plt.plot(r/2, gross, "rx--", markevery=me, label="Gross",
           markerfacecolor='none', markeredgecolor='red', markeredgewidth=1)
A_plt.legend(loc='lower right', ncol=1).draw_frame(False) #get_frame().set_alpha(0.5)
A_plt.yaxis.set_major_locator(pylab.MaxNLocator(integer=True, prune='upper'))
pylab.xlim(showrmin/2, showrmax/2)
#matplotlib.ticks(arange(0.5, 1.5, 3.5))

pylab.ylabel("$g^A$")

S_plt = pylab.subplot(3, 1, 2)
S_plt.axvline(x=radius/2, color='k', linestyle=':')
S_plt.plot(r_mc[gS_mc<5]/2, gS_mc[gS_mc<5], "g-", label="$g_\sigma^S$ MC")
S_plt.plot(r[showrmin<=r]/2, gS[showrmin<=r], "go--", markevery=me, label="$g_\sigma^S$ this work")
#S_plt.plot(r_2[showrmin<=r_2]/2,gS_2[showrmin<=r_2], "g.--",markevery=me,label="$g_\sigma^S$ (White Bear mark II)")
S_plt.plot(r/2, gyuwu, "gx--", markevery=me, label="Yu and Wu")
S_plt.legend(loc='lower right', ncol=1).draw_frame(False) #get_frame().set_alpha(0.5)
if int(ffdigit) == 4 and  int(radiusname) == 6:
        S_plt.yaxis.set_major_locator(pylab.MaxNLocator(integer=True, prune='both'))
else:
    S_plt.yaxis.set_major_locator(pylab.MaxNLocator(integer=True, prune='upper'))

pylab.xlim(showrmin/2, showrmax/2)

pylab.ylabel("$g^S$")

xticklabels = A_plt.get_xticklabels() + S_plt.get_xticklabels()
pylab.setp(xticklabels, visible=False)

pylab.savefig(pdffilename)

pylab.show()

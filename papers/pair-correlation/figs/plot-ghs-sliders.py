#!/usr/bin/python

from __future__ import division
# We need the following two lines in order for matplotlib to work
# without access to an X server.
import matplotlib, sys, os.path

if len(sys.argv) < 2 or sys.argv[1]!="show" :
  matplotlib.use('Agg')

from pylab import *
from scipy.optimize import leastsq

sigma = 2

fig = figure(1)
ax = fig.add_subplot(111)
ax.set_title('$g_{HS}(r)$') #radial distribution for hard spheres
ax.axvline(x=sigma, color='k', linestyle=':')
ax.axhline(y=1, color='k', linestyle=':')

x = rand(5)*5

x[0] = 1.706
x[1] = 1.358
x[2] = 1.567

x[3] = 0.675
x[4] = 0.463


colors = ['r', 'g', 'b', 'c', 'm', 'k', 'y']*2
ff = array([.1, .2, .3, .4])
#ff = array([.05, .1, .15, .2, .25, .3, .35, .4, .45, .5])
able_to_read_file = True


def read_ghs(base, ff):
  mcdatafilename = "%s-%4.2f.dat" % (base, ff)
  if (os.path.isfile(mcdatafilename) == False):
    print("File does not exist: ", mcdatafilename)
    global able_to_read_file
    able_to_read_file = False
    return 0, 0

  mcdata = loadtxt(mcdatafilename)
  print('Using', mcdatafilename, 'for filling fraction', ff)
  r_mc = mcdata[:, 0]
  n_mc = mcdata[:, 1]
  ghs = n_mc/ff
  return r_mc, ghs


# READ DATA
ghs = [0]*len(ff)
#ghslores = [0]*len(ff)
eta = [0]*len(ff)


for i in range(len(ff)):
    r_mc, ghs[i] = read_ghs("figs/gr", ff[i])
    if able_to_read_file == False:
        break
    #r_mclores, ghslores[i] = read_ghs("grlores", ff[i])
    figure(1)
    ax.plot(r_mc, ghs[i], colors[i]+":", label='ghs at filling fraction %.2f'%ff[i])
    # The following is the Monte Carlo approximation of the
    # distribution function at contact.  This gives us an answer with
    # no systematic error (well, very little, and what we have is due
    # to the finite bin size), and if we wait long enough the
    # statistical error should become negligible.
    #gsig[i] = ghs[i].max()
    # The following is the Carnahan Starling formula for the
    # distribution function at contact.  This is approximate, but it
    # is a good approximation.
    eta[i] = ff[i]
    r = r_mc

def evalg(xnew, eta, r):
  return evalg_nosquare(xnew, eta, r)

toprint = True

def evalg_nosquare(xnew, eta, r):
  global toprint
  z = r - sigma
  hsigma = (1 - 0.5*eta)/(1-eta)**3 - 1
  density = 3/4/pi*eta
  rhs = (1-eta)**4/(1+4*eta+4*eta**2-4*eta**3+eta**4)/3

  a0 = xnew[0]
  a1 = 0 # this parameter is constrained via integral
  a2 = xnew[1]
  a3 = xnew[2]
  a4 = 0 # constrained by slope at sigma
  a5 = xnew[3]
  a6 = xnew[4]

  int_h0 = 4*pi*hsigma*(2 + sigma*a0*(2 + sigma*a0))/a0**3

  int_h1_over_a1 = 4*pi*a2* \
      (sigma**2*a2**4 + 2*a2**2* \
         (-1 + sigma*a3*(2 + sigma*a3)) + a3**2*(6 + sigma*a3*(4 + sigma*a3))) \
         /(a2**2 + a3**2)**3

  int_h2_over_a4 = 4*pi*a5* \
      (sigma**2*a5**4 + 2*a5**2* \
         (-1 + sigma*a6*(2 + sigma*a6)) + a6**2*(6 + sigma*a6*(4 + sigma*a6))) \
         /(a5**2 + a6**2)**3

  A = (rhs-1)/density - int_h0
  B = int_h2_over_a4
  C = int_h1_over_a1

  a1 = (A/C - B*hsigma/C/a5*(-1-hsigma + a0))/(1 - B*a2/C/a5)

  a4 = hsigma/a5*(-1 - hsigma + a0 - a1*a2/hsigma) # this matches slope at x = sigma


  if toprint:
    print(eta, a1, a4, a1/a4)
    toprint = False

  f0 = hsigma
  j0 = exp(-a0*z)

  f1 = a1
  j1 = sin(a2*z)*exp(-a3*z)

  f2 = a4
  j2 = sin(a5*z)*exp(-a6*z)

  return 1 + f0*j0 + f1*j1 + f2*j2

def dist(x):
  # function with x[i] as constants to be determined
  g = zeros_like(etaconcatenated)
  for i in range(len(g)):
    g[i] = evalg(x, etaconcatenated[i], rconcatenated[i])
  return g

def dist2(x):
  return dist(x) - ghsconcatenated


ghsconcatenated = ghs[0]
for i in range(1, len(ff)):
  ghsconcatenated = concatenate((ghsconcatenated, ghs[i]))

etaconcatenated = [0]*len(r)*len(eta)
j = 0
while (j < len(eta)):
  i = 0
  while (i < len(r)):
    etaconcatenated[i + j*len(r)] = eta[j]
    i += 1
  j += 1

rconcatenated = [0]*len(r)*len(eta)
j = 0
while (j < len(eta)):
  i = 0
  while (i < len(r)):
    rconcatenated[i + j*len(r)] = r[i]
    i += 1
  j += 1



g=dist(x)

toprint = True
# make plots:
plots = [0]*len(ff)
for i in range(len(ff)):
  plots[i], = ax.plot(r_mc, g[i*len(r):(i+1)*len(r)], colors[i]+'-', label='g at filling fraction %.2f'%ff[i])

# sliders
y0 = .025
dy = .025
sliders_ax = [0]*len(x)
sliders = [0]*len(x)
for i in range(len(x)):
  sliders_ax[i] = axes([0.25, y0 + i*dy, 0.5, dy], axisbg='slategray')
  slidername = 'x[%i]' %i
  sliders[i] = Slider(sliders_ax[i], slidername, -5.00, 5.00, valinit = x[i])

chi2 = sum(dist2(x)**2)
def update(val):
  global x
  ax.collections=[]
  for i in range(len(x)):
    x[i] = sliders[i].val
  chi2 = sum(dist2(x)**2)

  g = dist(x)
  for i in range(len(ff)):
    plots[i].set_data(r_mc, g[i*len(r):(i+1)*len(r)])
    #ax.plot(r_mc, g[i*len(r):(i+1)*len(r)], colors[i]+'--',label='g at filling fraction %.2f'%ff[i])
  ax.set_title('$g_{HS}(r)$, $\\chi^2 %.2f$' %chi2)
  draw()

for i in range(len(x)):
  sliders[i].on_changed(update)


figure(1)
ax.set_xlim(2, 6.5)
ax.set_ylim(0., 3.5)
ax.set_title('$g_{HS}(r)$, $\\chi^2 %.2f$' %chi2)
ax.set_xlabel(r"$r/R$")
ax.set_ylabel("$g(r)$")

ax.axhline(y=0)
ax.legend(loc='best')
show()

from __future__ import division
import matplotlib, sys
if 'show' not in sys.argv:
  matplotlib.use('Agg')
import SW
import numpy as np
import matplotlib.pyplot as plt

# Plot vs n
R = 1 # HS radius
eta_conv = SW.sigma**3*np.pi/6
nmax = 0.9/eta_conv
n = nmax*np.exp(np.arange(-15, 0, 1e-3))

def plotPhi(T, npart):
    plt.plot(n*eta_conv, SW.phi(T, n, npart))
    plt.ylabel(r'$\phi$ /SW units')

    plt.xlabel(r'$\eta$')
    plt.title('SW; T = %0.2f '%T)
    plt.xlim(0, 0.4)
    plt.ylim(-0.005, 0.015)

def plotF(T):
    plt.subplot(211)
    plt.plot(n*eta_conv, SW.f(T, n))
    plt.ylabel(r'$f$ (SW units)')
    plt.title('T=%0.2f'%T)

    plt.subplot(212)
    plt.plot(n*eta_conv, SW.df_dn(T, n))
    plt.ylabel(r'$\frac{df}{dn}$ (SW units)')

plotPhi(0.94, 0.0386417984268)

#!/usr/bin/python2
import matplotlib, sys
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy

matplotlib.rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
matplotlib.rc('text', usetex=True)

import styles
import readandcompute

if len(sys.argv) != 5:
    print 'useage: %s ww ff N methods' % sys.argv[0]
    exit(1)

ww = float(sys.argv[1])
#arg ww = [1.3, 1.5, 2.0, 3.0]

ff = float(sys.argv[2])
#arg ff = [0.3]

N = float(sys.argv[3])
#arg N = range(5,31)

methods = eval(sys.argv[4])
#arg methods = [["wang_landau","simple_flat","tmmc","oetmmc"]]

# input: ["../histogram/data/periodic-ww%04.2f-ff%04.2f-N%i-%s-%s.dat" % (ww, ff, N, method, data) for method in methods for data in ["E","lnw"]]

for method in set(methods):

    T, U, CV, S, min_T = readandcompute.T_u_cv_s_minT('../histogram/data/periodic-ww%04.2f-ff%04.2f-N%i-%s' % (ww, ff, N, method))

    plt.figure('u')
    plt.plot(T,U/N,styles.plot(method),label=styles.title(method))

    plt.figure('hc')
    plt.plot(T,CV/N,styles.plot(method),label=styles.title(method))

    plt.figure('s')
    plt.plot(T,S/N,styles.plot(method),label=styles.title(method))

plt.figure('u')
plt.title('Specific internal energy for $\lambda=%g$, $\eta=%g$, and $N=%i$' % (ww, ff, N))
plt.xlabel('$kT/\epsilon$')
plt.ylabel('$U/N\epsilon$')
plt.legend(loc='best')
plt.axvline(min_T,linewidth=1,color='k',linestyle=':')
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-N%i-u.pdf" % (ww*100, ff*100, N))

plt.figure('hc')
plt.title('Specific heat capacity for $\lambda=%g$, $\eta=%g$, and $N=%i$' % (ww, ff, N))
plt.ylim(0)
plt.xlabel('$kT/\epsilon$')
plt.ylabel('$C_V/Nk$')
plt.legend(loc='best')
plt.axvline(min_T,linewidth=1,color='k',linestyle=':')
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-N%i-hc.pdf" % (ww*100, ff*100, N))

plt.figure('s')
plt.title('Configurational entropy for $\lambda=%g$, $\eta=%g$, and $N=%i$' % (ww, ff, N))
plt.xlabel(r'$kT/\epsilon$')
plt.ylabel(r'$S_{\textit{config}}/Nk$')
plt.legend(loc='best')
plt.axvline(min_T,linewidth=1,color='k',linestyle=':')
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-N%i-S.pdf" % (ww*100, ff*100, N))
#!/usr/bin/python2
import matplotlib, sys
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy
import styles

if len(sys.argv) != 6:
    print 'useage: %s ww ff N methods seed' % sys.argv[0]
    exit(1)

ww = float(sys.argv[1])
#arg ww = [1.3, 1.5, 2.0, 3.0]

ff = float(sys.argv[2])
#arg ff = [0.1, 0.2, 0.3, 0.4]

N = int(sys.argv[3])
#arg N = list(range(5,21))+[100, 200, 1000]

methods = eval(sys.argv[4])
#arg methods = [["nw","wang_landau","simple_flat","tmmc","oetmmc"]]

seed = int(sys.argv[5])
#arg seed = [0]

# input: ["data/s%03d/periodic-ww%04.2f-ff%04.2f-N%i-%s-%s.dat" % (seed, ww, ff, N, method, data) for method in methods for data in ["E","lnw"]]

minlog = 0
for method in methods:
    e_hist = numpy.loadtxt("data/s%03d/periodic-ww%04.2f-ff%04.2f-N%i-%s-E.dat"
                           % (seed, ww, ff, N, method))
    lnw = numpy.loadtxt("data/s%03d/periodic-ww%04.2f-ff%04.2f-N%i-%s-lnw.dat"
                        % (seed, ww, ff, N, method))
    energy = -e_hist[:,0]/N
    log10w = lnw[e_hist[:,0].astype(int),1]*numpy.log10(numpy.exp(1))
    log10_dos = numpy.log10(e_hist[:,1]) - log10w
    log10_dos -= log10_dos.max()
    if log10_dos.min() < minlog:
        minlog = log10_dos.min()
    plt.figure('dos')
    plt.plot(energy, log10_dos, styles.dots(method),label=styles.title(method))

    log10w += log10w.min()
    if log10w.min() < minlog:
        minlog = log10w.min()
    plt.figure('w')
    plt.plot(energy, -log10w, styles.dots(method),label=styles.title(method))


def tentothe(n):
    if n == 0:
        return '1'
    if n == 10:
        return '10'
    if int(n) == n:
        return r'$10^{%d}$' % n
    return r'$10^{%g}$' % n


plt.figure('dos')
plt.ylim(minlog, 0)
locs, labels = plt.yticks()
newlabels = [tentothe(n) for n in locs]
plt.yticks(locs, newlabels)
plt.ylim(minlog, 0)

plt.xlabel('$E/N\epsilon$')
plt.ylabel('$DoS$')
plt.title('Density of states for $\lambda=%g$, $\eta=%g$, and $N=%i$' % (ww, ff, N))
plt.legend(loc='best')
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-N%i-dos.pdf" % (ww*100, ff*100, N))


plt.figure('w')
plt.ylim(minlog, 0)
locs, labels = plt.yticks()
newlabels = [tentothe(n) for n in locs]
plt.yticks(locs, newlabels)
plt.ylim(minlog, 0)

plt.xlabel('$E/N\epsilon$')
plt.ylabel('$1/w$')
plt.title('Weighting functions for $\lambda=%g$, $\eta=%g$, and $N=%i$' % (ww, ff, N))
plt.legend(loc='best')
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-N%i-weights.pdf" % (ww*100, ff*100, N))


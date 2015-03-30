#!/usr/bin/python2
import matplotlib, sys
if 'show' not in sys.argv:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy, glob, re, string
import styles

matplotlib.rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
matplotlib.rc('text', usetex=True)

if len(sys.argv) not in [5,6]:
    print 'useage: %s ww ff Ns methods show' % sys.argv[0]
    exit(1)

ww = float(sys.argv[1])
#arg ww = [1.3, 1.5, 2.0, 3.0]

ff = float(sys.argv[2])
#arg ff = [0.1, 0.2, 0.3, 0.4]

all_Ns = eval(sys.argv[3])
#arg all_Ns = [[5,10,20]]

methods = eval(sys.argv[4])
#arg methods = [["wang_landau","simple_flat","tmmc","oetmmc","wang_landau_oe","simple_flat_oe","tmmc_oe","oetmmc_oe"]]

# input: ["data/periodic-ww%04.2f-ff%04.2f-N%i-%s-%s.dat" % (ww, ff, N, method, dat) for method in methods for N in all_Ns for dat in ['ps', 'lnw', 'E']]

N_regex = re.compile(r'-N([0-9]+)')
initialization_iters_regex = re.compile(r'# iterations:\s+([0-9]+)')

plt.title('Scaling for $\lambda=%g$, $\eta=%g$' % (ww, ff))
init_iters = {}
Emins = {}
samples = {}
Ns = {}
for method in methods:
  init_iters[method] = []
  Emins[method] = []
  samples[method] = []
  N_files = glob.glob("data/periodic-ww%04.2f-ff%04.2f-N*-%s-lnw.dat" % (ww, ff, method))
  Ns[method] = [ int(N_file.split('-')[-3][1:]) for N_file in N_files ]
  Ns[method].sort()
  for N in Ns[method]:
    filename = "data/periodic-ww%04.2f-ff%04.2f-N%d-%s-lnw.dat" % (ww, ff, N, method)
    wildfilename = "data/periodic-ww%04.2f-ff%04.2f-N%d-%s-%%s.dat" % (ww, ff, N, method)

    with open(filename, 'r') as content_file:
        content = content_file.read()
    init_iters[method].append(int(initialization_iters_regex.findall(content)[0]))

    E_data = numpy.loadtxt(wildfilename % 'E', ndmin=2)
    Emins[method].append(E_data[:, 0].max())

    sample_data = numpy.loadtxt(wildfilename % 'ps', ndmin=2)
    samples[method].append(sample_data[len(sample_data[:,1])-1, 1])

  plt.figure('iters')
  plt.semilogy(Ns[method], init_iters[method], styles.color(method)+'.-',
               label=styles.title(method))
  plt.figure('emin')
  plt.plot(Ns[method], Emins[method],styles.color(method)+'.-', label=styles.title(method))

plt.figure('iters')
plt.xlabel('$N$')
plt.ylabel('Initialization iterations')
plt.legend(loc='best').get_frame().set_alpha(0.25)
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-scaling.pdf" % (ww*100, ff*100))

plt.figure('emin')
plt.xlabel('$N$')
plt.ylabel('Emin')
plt.legend(loc='best').get_frame().set_alpha(0.25)
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-scaling-emin.pdf" % (ww*100, ff*100))

texmethods = [m.replace('_', ' ') for m in methods]

tex = open("figs/scaling-table-ww%02.0f-ff%02.0f.tex" % (ww*100, ff*100), "w")
tex.write(r"""
\begin{tabular}{c|%s}
""" % ("c"*len(methods)))
for method in texmethods:
    tex.write(" & " +method)
tex.write(r"""\\
\hline\hline
""")

for i in range(len(all_Ns)):
    N = all_Ns[i]
    tex.write(r""" N = %d \\
  initialization""" % N)

    tex.write(string.join([" & %d " % init_iters[m][i] for m in methods]))
    tex.write("\\\\\n")

    tex.write('Emin')
    tex.write(string.join([" & %d " % Emins[m][i] for m in methods]))
    tex.write("\\\\\n")

    tex.write('samples')
    tex.write(string.join([" & %d " % samples[m][i] for m in methods]))
    tex.write("\\\\\n")

tex.write(r"""\end{tabular}
""")

# input: ["figs/error-table-ww%02.0f-ff%02.0f-%i.dat" % (ww*100, ff*100, N) for N in all_Ns]

cv_errors = {}
S_errors = {}
u_errors = {}
min_Ts = []
for N in all_Ns:
    f = open("figs/error-table-ww%02.0f-ff%02.0f-%i.dat"
             % (ww*100, ff*100, N))
    for line in f.read().split('\n'):
        if 'min_T' in line:
            min_Ts.append(float(line.split()[-1]))
        if len(line) > 0 and line[0] != '#':
            line = line.split()
            method = line[0]
            print 'method', method, 'u_error', line[1]
            if method not in u_errors:
                u_errors[method] = numpy.array([[N, float(line[1])]])
            else:
                u_errors[method] = numpy.vstack([u_errors[method],
                                                 numpy.array([[N, float(line[1])]])])
            if method not in cv_errors:
                cv_errors[method] = numpy.array([[N, float(line[3])]])
            else:
                cv_errors[method] = numpy.vstack([cv_errors[method],
                                                  numpy.array([[N, float(line[3])]])])
            if method not in S_errors:
                S_errors[method] = numpy.array([[N, float(line[5])]])
            else:
                S_errors[method] = numpy.vstack([S_errors[method],
                                                 numpy.array([[N, float(line[5])]])])

min_T = max(min_Ts)
if len(set(min_Ts)) > 1:
    print('WARNING: There are minimum temperatures in error tables.')
    print('         The maximum error scaling figures are not to be trusted!!!')
    # fixme: do more than just spit out a warning.
    #   Make one figure for each minimum temperature?

plt.figure()
for method in u_errors.keys():
    plt.plot(u_errors[method][:,0], u_errors[method][:,1],
             '.'+styles.plot(method),label=styles.title(method))

plt.title('Maximum error with $\lambda=%g$, $\eta=%g$, and $T_{min}=%g$' % (ww, ff, min_T))
plt.xlabel('$N$')
plt.ylabel('$\\Delta U/N\epsilon$')
plt.legend(loc='best').get_frame().set_alpha(0.25)
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-u_errors.pdf" % (ww*100, ff*100))

plt.figure()
for method in cv_errors.keys():
    plt.plot(cv_errors[method][:,0], cv_errors[method][:,1],
             '.'+styles.plot(method),label=styles.title(method))

plt.title('Maximum error with $\lambda=%g$, $\eta=%g$, and $T_{min}=%g$' % (ww, ff, min_T))
plt.xlabel('$N$')
plt.ylabel('$\\Delta C_V/N\epsilon$')
plt.legend(loc='best').get_frame().set_alpha(0.25)
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-cv_errors.pdf" % (ww*100, ff*100))

plt.figure()
for method in S_errors.keys():
    plt.plot(S_errors[method][:,0], S_errors[method][:,1],
             '.'+styles.plot(method),label=styles.title(method))

plt.title('Maximum error with $\lambda=%g$, $\eta=%g$, and $T_{min}=%g$' % (ww, ff, min_T))
plt.xlabel('$N$')
plt.ylabel(r'$\Delta S_{\textit{config}}/Nk$')
plt.legend(loc='best').get_frame().set_alpha(0.25)
plt.tight_layout(pad=0.2)
plt.savefig("figs/periodic-ww%02.0f-ff%02.0f-S_errors.pdf" % (ww*100, ff*100))

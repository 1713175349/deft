#!/usr/bin/python3

import numpy as np
import matplotlib.pyplot as plt
import os

T = np.arange(0.01, 0.06000001, 0.0005)

fnames = [
    '/home/droundy/src/sad-monte-carlo/tiny-lj-benchmark-0.001',

    '/home/jordan/sad-monte-carlo/lj-wl-31-bin001',
    '/home/jordan/sad-monte-carlo/lj-wl-31-bin002',
    '/home/jordan/sad-monte-carlo/lj-wl-31-bin0005',

    '/home/jordan/sad-monte-carlo/lj-inv-t-wl-31-bin001',
    '/home/jordan/sad-monte-carlo/lj-inv-t-wl-31-bin002',
    '/home/jordan/sad-monte-carlo/lj-inv-t-wl-31-bin0005',

    '/home/jordan/sad-monte-carlo/lj-samc-31-1e5-bin001',
    '/home/jordan/sad-monte-carlo/lj-samc-31-1e5-bin002',
    '/home/jordan/sad-monte-carlo/lj-samc-31-1e5-bin0005',

    '/home/jordan/sad-monte-carlo/lj-samc-31-1e6-bin001',
    '/home/jordan/sad-monte-carlo/lj-samc-31-1e6-bin002',
    '/home/jordan/sad-monte-carlo/lj-samc-31-1e6-bin0005',

    '/home/jordan/sad-monte-carlo/lj-samc-31-1e7-bin001',
    '/home/jordan/sad-monte-carlo/lj-samc-31-1e7-bin002',
    '/home/jordan/sad-monte-carlo/lj-samc-31-1e7-bin0005',

    '/home/jordan/sad-monte-carlo/lj-sad-31-bin001',
    '/home/jordan/sad-monte-carlo/lj-sad-31-bin002',
]

bench = fnames[0]

CV = None

def heat_capacity(T, E, S):
    C = np.zeros_like(T)
    for i in range(len(T)):
        boltz_arg = S - E/T[i]
        P = np.exp(boltz_arg - boltz_arg.max())
        P = P/P.sum()
        U = (E*P).sum()
        C[i] = ((E-U)**2*P).sum()/T[i]**2
    return C + 31*1.5

datadir = 'data/lj31/'
os.makedirs(datadir, exist_ok=True)

for fname in fnames:
    print(fname)
    time = np.loadtxt(fname+'.time')
    my_energy = np.loadtxt(fname+'.energy')
    my_entropy = np.loadtxt(fname+'.entropy')

    if CV is None:
        Ebest = my_energy;
        Sbest = my_entropy[-1,:]
        CV = heat_capacity(T, Ebest, Sbest)
        np.savetxt(datadir+'bench-cv.txt',
                   np.array([T, CV]).transpose(),
                   fmt='%.4g', # good enough for our plot
        );

    cv_error = []
    cv_max_error = []
    myt = []
    for t in range(len(my_entropy[:,0])):
        if time[t] < 1e7:
            continue
        myt.append(time[t])
        mycv = heat_capacity(T, my_energy, my_entropy[t,:])
        plt.clf()
        plt.plot(T, mycv)
        plt.title(fname+' '+str(time[t]))
        plt.pause(0.01)

        err = 0
        norm = 0
        for j in range(1, len(mycv)):
            err += abs(CV[j]-mycv[j])
            norm += 1.0
        cv_error.append(err/norm)
        cv_max_error.append(abs(CV-mycv).max())
        if time[t] == 1e12:
            np.savetxt(datadir+os.path.basename(fname)+'-cv.txt',
                       np.array([T, mycv]).transpose(),
                       fmt='%.4g', # good enough for our plot
            );

    np.savetxt(datadir+os.path.basename(fname)+'-cv-error.txt',
               np.array([myt, cv_error, cv_max_error]).transpose(),
               fmt='%.3g', # low resolution is good enough for error data.
    );

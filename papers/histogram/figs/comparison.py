from __future__ import division
import numpy, sys, os
import matplotlib.pyplot as plt
import readnew
from glob import glob

if os.path.exists('../data'):
    os.chdir('..')

energy = int(sys.argv[1])
reference = sys.argv[2]
filebase = sys.argv[3]
methods = [ '-sad3', '-sad3-s1', '-sad3-s2',
            '-tmmc', '-tmi', '-tmi2', '-tmi3', '-toe', '-toe2', '-toe3',
            '-vanilla_wang_landau', '-sad']
if 'allmethods' not in sys.argv:
    methods = ['-sad3', '-sad3-s2', '-sad3-s5', '-sad3-s6', '-tmmc', '-vanilla_wang_landau', '-vanilla_wang_landau-minE', '-vanilla_wang_landau-s2', '-sad3-test', '-sad3-T13', '-one_over_t_wang_landau-T13-t',
               '-vanilla_wang_landau-T13', '-vanilla_wang_landau-T13-slow', '-n256-tmmc']
fast_methods = [m+'-fast' for m in methods]
slow_methods = [m+'-slow' for m in methods]
methods = methods + fast_methods + slow_methods

def running_mean(x, N):
    cumsum = numpy.cumsum(numpy.insert(x, 0, 0)) 
    averaged = (cumsum[N:] - cumsum[:-N]) / N
    return numpy.concatenate((x[:len(x)-len(averaged)], averaged))

# For WLTMMC compatibility with LVMC
lvextra = glob('data/%s-wltmmc*-movie' % filebase)
split1 = [i.split('%s-'%filebase, 1)[-1] for i in lvextra]
split2 = [i.split('-m', 1)[0] for i in split1]
for j in range(len(split2)):
    methods.append('-%s' %split2[j])

# For SAMC compatibility with LVMC
lvextra1 = glob('data/%s-samc*-movie' % filebase)
split3 = [i.split('%s-'%filebase, 1)[-1] for i in lvextra1]
split4 = [i.split('-m', 1)[0] for i in split3]
for j in range(len(split4)):
    methods.append('-%s' %split4[j])

print(methods)

ref = reference
if ref[:len('data/')] != 'data/':
    ref = 'data/' + ref
maxref = int(readnew.max_entropy_state(ref))
minref = int(readnew.min_important_energy(ref))
n_energies = int(minref - maxref+1)
print(maxref, minref)
try:
    eref, lndosref, Nrt_ref = readnew.e_lndos_ps(ref)
except:
    eref, lndosref = readnew.e_lndos(ref)

for method in methods:
    dirname = 'data/comparison/%s%s' % (filebase, method)
    dirnametm = 'data/comparison/%s%s-tm' % (filebase, method)
    try:
        r = glob('data/%s%s-movie/*lndos.dat' % (filebase, method))
        if len(r)==0:
            # print(" ... but it has no data in data/%s%s-movie/*lndos.dat" % (filebase,method))
            continue
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if not os.path.exists(dirnametm):
            os.makedirs(dirnametm)
        #wl_factor = numpy.zeros(len(r))
        iterations = numpy.zeros(len(r))
        Nrt_at_energy = numpy.zeros(len(r))
        maxentropystate = numpy.zeros(len(r))
        minimportantenergy = numpy.zeros(len(r))
        erroratenergy = numpy.zeros(len(r))
        errorinentropy = numpy.zeros(len(r))
        maxerror = numpy.zeros(len(r))

        erroratenergytm = numpy.zeros(len(r))
        errorinentropytm = numpy.zeros(len(r))
        maxerrortm = numpy.zeros(len(r))

        for i, f in enumerate(sorted(r)):
            e, lndos, Nrt, lndostm = readnew.e_lndos_ps_lndostm(f)
            maxentropystate[i] = readnew.max_entropy_state(f)
            minimportantenergy[i] = readnew.min_important_energy(f)

            #wl_factor[i] = readnew.wl_factor(f)
            iterations[i] = readnew.iterations(f)
            Nrt_at_energy[i] = Nrt[energy]
            # The following norm_factor is designed to shift our lndos
            # curve in such a way that our errors reflect the ln of the
            # error in the predicted histogram.  i.e. $\Delta S$ a.k.a.
            # doserror = -ln H where H is the histogram that would be
            # observed when running with weights determined by lndos.
            # norm_factor = numpy.log(numpy.sum(numpy.exp(lndos[maxref:minref+1] - lndosref[maxref:minref+1]))/n_energies)

            # below just set average S equal between lndos and lndosref
            index_maxref = numpy.argwhere(eref == -maxref)[0][0]
            index_minref = numpy.argwhere(eref == -minref)[0][0]
            index_max = numpy.argwhere(e == -maxref)[0][0]
            index_min = numpy.argwhere(e == -minref)[0][0]
            norm_factor = numpy.mean(lndos[index_max:index_min+1]) - numpy.mean(lndosref[index_maxref:index_minref+1])
            #print index_maxref
            #print index_minref
            #print lndosref[index_maxref:index_minref]
            #print lndos[index_maxref:index_minref]
            doserror = lndos[index_max:index_min+1] - lndosref[index_maxref:index_minref+1] - norm_factor
            errorinentropy[i] = numpy.sum(abs(doserror))/len(doserror)
            erroratenergy[i] = doserror[energy-maxref]
            # the following "max" result is independent of how we choose
            # to normalize doserror, and represents the largest ratio
            # of fractional errors in the actual (not ln) DOS.
            maxerror[i] = numpy.amax(doserror) - numpy.amin(doserror)
            
            if lndostm is not None:
                norm_factor = numpy.mean(lndos[index_max:index_min+1]) - numpy.mean(lndosref[index_maxref:index_minref+1])
                doserror = lndos[index_max:index_min+1] - lndosref[index_maxref:index_minref+1] - norm_factor
                errorinentropytm[i] = numpy.sum(abs(doserror))/len(doserror)
                erroratenergytm[i] = doserror[energy-maxref]
                # the following "max" result is independent of how we choose
                # to normalize doserror, and represents the largest ratio
                # of fractional errors in the actual (not ln) DOS.
                maxerrortm[i] = numpy.amax(doserror) - numpy.amin(doserror)

        # The following is intended for testing whether there is a
        # systematic error in any of our codes.
        
        #numpy.savetxt('%s/error-vs-energy.txt' %(dirname),
                    #numpy.c_[eref, doserror],
                    #fmt = ('%.4g'),
                    #delimiter = '\t', header = 'E\t Serror')
        i = 1
        while i < len(iterations) and iterations[i] >= iterations[i-1]:
            num_frames_to_count = i+1
            i+=1
        #wl_factor = wl_factor[:num_frames_to_count]
        iterations = iterations[:num_frames_to_count]
        minimportantenergy = minimportantenergy[:num_frames_to_count]
        maxentropystate = maxentropystate[:num_frames_to_count]
        Nrt_at_energy = Nrt_at_energy[:num_frames_to_count]
        erroratenergy = erroratenergy[:num_frames_to_count]
        errorinentropy = errorinentropy[:num_frames_to_count]
        windows = int(len(iterations)/10 + 1)
        windows = 10
        maxerror = maxerror[:num_frames_to_count]
        #uncomment the following line for windowed averages
        #maxerror = running_mean(maxerror[:num_frames_to_count],windows)

        erroratenergytm = erroratenergytm[:num_frames_to_count]
        errorinentropytm = errorinentropytm[:num_frames_to_count]
        maxerrortm = maxerrortm[:num_frames_to_count]

        print('saving to', dirname)
        numpy.savetxt('%s/energy-%d.txt' %(dirname, energy),
                      numpy.c_[Nrt_at_energy, erroratenergy],
                      fmt = ('%.4g'),
                      delimiter = '\t', header = 'round trips\t doserror')
        numpy.savetxt('%s/errors.txt' %(dirname),
                      numpy.c_[iterations, errorinentropy, maxerror],
                      fmt = ('%.4g'),
                      delimiter = '\t',
                      header = 'iterations\t errorinentropy\t maxerror\t(generated with python %s' % ' '.join(sys.argv))
        #if not numpy.isnan(numpy.sum(wl_factor)):
            #numpy.savetxt('%s/wl-factor.txt' %(dirname),
                        #numpy.c_[iterations, wl_factor],
                        #fmt = ('%.4g'),
                        #delimiter = '\t',
                        #header = 'iterations\t wl_factor\t(generated with python %s' % ' '.join(sys.argv))

        if lndostm is not None:
            print('saving to', dirnametm)
            numpy.savetxt('%s/energy-%d.txt' %(dirnametm, energy),
                        numpy.c_[Nrt_at_energy, erroratenergytm],
                        fmt = ('%.4g'),
                        delimiter = '\t', header = 'round trips\t doserror')
            numpy.savetxt('%s/errors.txt' %(dirnametm),
                        numpy.c_[iterations, errorinentropytm, maxerrortm],
                        fmt = ('%.4g'),
                        delimiter = '\t',
                        header = 'iterations\t errorinentropy\t maxerror\t(generated with python %s' % ' '.join(sys.argv))
            #if not numpy.isnan(numpy.sum(wl_factor)):
                #numpy.savetxt('%s/wl-factor.txt' %(dirnametm),
                        #numpy.c_[iterations, wl_factor],
                        #fmt = ('%.4g'),
                        #delimiter = '\t',
                        #header = 'iterations\t wl_factor\t(generated with python %s' % ' '.join(sys.argv))
    except:
        print('I had trouble with', method)
        raise

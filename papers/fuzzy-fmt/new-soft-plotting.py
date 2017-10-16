#!/usr/bin/env python2
from __future__ import division
from mpl_toolkits.mplot3d import Axes3D
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import math
import argparse
########################################################################
## This script reads data from files and plots for new-soft
########################################################################
#Global Constants
x = 0
y = 1
z = 2

# Default data sets to pull from. 
rhoDefault = [0.6,0.7,0.8,0.9,0.91,0.92,0.93,0.94,0.95,0.96,0.97,0.98,\
    0.99,1.0,1.1,1.2,1.3,1.4]
TDefault = [1.0]

def plotPressure(rho,T):
	plt.figure()
	for density in rho:
		pressArray = []
		for temp in T:
			pressure = np.loadtxt('data2/ff-'+str(density)+\
                '_temp-'+str(temp)+'-press.dat')
                
                if density == 0.95:
                    pressure = float(pressure*1e10/3664101397)
                elif density == 0.96:
                    pressure = float(pressure*1e10/3742376538)
                elif density == 0.97:
                    pressure = float(pressure*1e10/3804308688)
                elif density == 0.98:
                    pressure = float(pressure*1e10/3964798948)
                elif density == 0.99:
                    pressure = float(pressure*1e10/4160728275)
                    
                pressArray.append(float(pressure))
                plt.plot(pressArray,density,'k.')
        plt.title('Density v. Pressure')
        plt.xlabel('Pressure')
        plt.ylabel('Density')

def plotPositions(rho,T):
	for density in rho:
		for temp in T:
			spheres = np.loadtxt('data2/ff-'+str(density)+\
                '_temp-'+str(temp)+'-pos.dat')
			fig = plt.figure()
			ax = fig.add_subplot(111, projection = '3d')
			ax.scatter(spheres[:,0],spheres[:,1],spheres[:,2],\
                c = 'r', marker ='o')
			ax.set_title('Positions at Temp: '+ str(temp)+\
                ' and Density: ' + str(density))
			ax.set_xlabel('x')
			ax.set_ylabel('y')
			ax.set_zlabel('z')


def plotRadialDF(rho,T):
	for density in rho:
		for temp in T:
			radialData  = np.loadtxt('data2/ff-'+str(density)+\
                '_temp-'+str(temp)+'-radial.dat')
			plt.figure()
			plt.plot(radialData[:,0],radialData[:,1]/(radialData[:,0]**2))
			plt.title('Sum of Spheres at a Radial Distance, non-averaged.\n'\
				'Temp: '+str(temp)+' and Density: ' +str(density))
			plt.xlabel('Radial Distance (r)')
			plt.ylabel('Number of Spheres at this distance')


#~ def plotEnergyPDF(rho,T):
	#~ for density in rho:
		#~ plt.figure()
		#~ for temp in T:
			#~ energyData = np.loadtxt('data/ff-'+str(density)+'_temp-'+\
                #~ str(temp)+'-energy.dat')
			#~ mu,e2 = energyData
			#~ sigma = np.sqrt(e2 - mu*mu)
			#~ x = np.linspace(mu - 4*sigma, mu + 4*sigma, 1000)
			#~ plt.plot(x,mlab.normpdf(x,mu,sigma))
			#~ plt.title('Energy Probability Distribution Function Density: '+\
                #~ str(density))
			#~ plt.xlabel('Total Internal Energy')
			#~ plt.ylabel('Probability')
            
def plotStructureFactor(rho,T):
    fig, ax = plt.subplots()
    for temp in T:
        for density in rho:
            structureData = np.loadtxt('data2/ff-'+str(density)+'_temp-'+\
                str(temp)+'-struc.dat')
            #~ print structureData[0][:]
            cax =ax.imshow(structureData[30:][30:], interpolation = 'nearest', cmap = "gnuplot")
            cbar = fig.colorbar(cax)
            ax.set_title('Structure Factor')
            ax.set_xlabel('kx')
            ax.set_ylabel('ky')

	
def plotDiffusionCoeff(rho,T):
    plt.figure()
    for temp in T:
        for density in rho:
            diffusionData = np.loadtxt('data2/ff-'+str(density)+'_temp-'+\
                str(temp)+'-dif.dat')
            plt.semilogy(density,diffusionData,'k.')
            plt.title('Diffusion Coefficient v. Reduced Density')
            plt.xlabel(r'$\rho*$')
            plt.ylabel('D (length/iteration)')
            #~ plt.ylim(0)

parser = argparse.ArgumentParser(description='Which plots to make.')
parser.add_argument('-p','--plot', metavar='PLOT', action ="store",
                    default='diffusion', help='the plot to make')
parser.add_argument('-r','--rho', metavar = 'RHO',type = float, nargs = "+",
                    default = rhoDefault, help = "List of densities.")
parser.add_argument('-t','--temp', metavar = 'TEMP',type = float, nargs = "+",
                    default = TDefault, help = "List of Temperatures")
args = parser.parse_args()

print("\nPlot: %s"%args.plot)
print'Densities: ',args.rho
print'Temperatures: ',args.temp
		
if args.plot.lower() == 'diffusion':
        plotDiffusionCoeff(args.rho,args.temp)
elif args.plot.lower() == 'pressure':
    plotPressure(args.rho,args.temp)
elif (len(args.rho) <=5 and len(args.temp) <= 5) \
    and args.plot.lower()!=('diffusion' or 'pressure'):
    #~ if args.plot.lower() == 'energy':
        #~ plotEnergyPDF(args.rho,args.temp)
            
    if args.plot.lower() == 'radial':
        plotRadialDF(args.rho,args.temp)		

    elif args.plot.lower() == 'positions':
        plotPositions(args.rho,args.temp)
    elif args.plot.lower() == 'structure':
        plotStructureFactor(args.rho,args.temp)
elif (len(args.rho) > 5 or len(args.temp) > 5) \
    and args.plot.lower()!=('diffusion' or 'pressure'):
    print("\nPlease reduce the amount of plots you want to make by "\
        "shortening the density or temperature list to less than 5 each."\
        "\nYou can end up plotting way too many figures.\n")
    print("Number of plots asked for, Density: %d, Temp: %d, Total:"\
    "%d\n\n"%(len(args.rho),len(args.temp),len(args.rho)*len(args.temp)))
else:
    print("\nOr Plot type %s not recognized.\nPlease enter either:\n"\
                "diffusion\npositions\npressure\nor radial\n"%args.plot)

plt.show()

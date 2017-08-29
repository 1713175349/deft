#!/usr/bin/env python2
from __future__ import division
from mpl_toolkits.mplot3d import Axes3D
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import math
########################################################################
## This script reads data from files and plots for new-soft
########################################################################
#Global Constants
x = 0
y = 1
z = 2

pmin = 0.1
pmax = 10.1
dp = 1.0

Tmin = 0.51
Tmax = 1.00
dT = 0.1

def plotPressure(pmin,pmax,dp,Tmin,Tmax,dT):
	nd = np.arange(pmin,pmax,dp)
	nT = np.arange(Tmin,Tmax,dT)
	pressure = np.zeros((len(nd),len(nT)))
	plt.figure()
	for density in nd:
		pressArray = []
		for temp in nT:
			pressure = np.loadtxt('data/ff-'+str(density)+'_temp-'+str(temp)+'-press.dat')
			pressArray.append(float(pressure))
		plt.semilogy(nT,pressArray,'.-')
		for i in range(len(pressArray)):
			plt.text(nT[i],pressArray[i],str(pressArray[i]),ha = 'center',va = 'center')
		plt.title('Pressure v. Temperature')
		plt.xlabel('Temperature')
		plt.ylabel('Pressure')
	plt.legend(nd[:],title='Reduced Density')
	


def plotPositions(pmin,pmax,dp,Tmin,Tmax,dT):
	for density in np.arange(pmin,pmax,dp):
		for temp in np.arange(Tmin,Tmax,dT):
			spheres = np.loadtxt('data/ff-'+str(density)+'_temp-'+str(temp)+'-pos.dat')
			fig = plt.figure()
			ax = fig.add_subplot(111, projection = '3d')
			ax.scatter(spheres[:,0],spheres[:,1],spheres[:,2],c = 'r', marker ='o')
			ax.set_title('Positions at Temp: '+ str(temp)+ ' and Density: ' + str(density))
			ax.set_xlabel('x')
			ax.set_ylabel('y')
			ax.set_zlabel('z')


def plotRadialDF(pmin,pmax,dp,Tmin,Tmax,dT):
	radboxes = np.zeros(1000)
	radheights = np.zeros(1000)
	for density in np.arange(pmin,pmax,dp):
		for temp in np.arange(Tmin,Tmax,dT):
			radialData  = np.loadtxt('data/ff-'+str(density)+'_temp-'+str(temp)+'-radial.dat')
			start = 0
			plt.figure()
			plt.plot(radialData[start:,0],radialData[start:,1])
			plt.title('Sum of Spheres at a Radial Distance, non-averaged.\n'\
				'Temp: '+str(temp)+' and Density: ' +str(density))
			plt.xlabel('Radial Distance (r)')
			plt.ylabel('Number of Spheres at this distance')


def plotEnergyPDF(pmin,pmax,dp,Tmin,Tmax,dT):
	for density in np.arange(pmin,pmax,dp):
		plt.figure()
		lis = []
		for temp in np.arange(Tmin,Tmax,dT):
			energyData = np.loadtxt('data/ff-'+str(density)+'_temp-'+str(temp)+'-energy.dat')
			mu,e2 = energyData

			lis.append(str(density)+"-"+str(temp))
			sigma = np.sqrt(e2 - mu*mu)
			x = np.linspace(mu - 4*sigma, mu + 4*sigma, 1000)
			plt.plot(x,mlab.normpdf(x,mu,sigma))
			plt.title('Energy Probability Distribution Function Density: '+str(density))
			plt.xlabel('Total Internal Energy')
			plt.ylabel('Probability')
		plt.legend(labels = lis[:],title = 'Density-Temp',loc = 0)
	
def plotDiffusionCoeff(pmin,pmax,dp,Tmin,Tmax,dT):
	for density in np.arange(pmin,pmax,dp):
			plt.figure()
			lis = []
			for temp in np.arange(Tmin,Tmax,dT):
				lis.append(str(temp))

				diffusionData = np.loadtxt('data/ff-'+str(density)+'_temp-'+str(temp)+'-dif.dat')
				plt.semilogx(diffusionData[1:,0],diffusionData[1:,1])
				plt.title('Diffusion Coefficient v Iterations\n'\
				' Density: '+str(density))
				plt.xlabel('Iterations')
				plt.ylabel('Diffusion Coefficient')
				plt.legend(labels = lis[:],title = 'Temp')

plotDiffusionCoeff(pmin,pmax,dp,Tmin,Tmax,dT)
#~ plotEnergyPDF(pmin,pmax,dp,Tmin,Tmax,dT)
#~ plotRadialDF(pmin,pmax,dp,Tmin,Tmax,dT)
#~ plotPositions(pmin,pmax,dp,Tmin,Tmax,dT)		# Careful w/ this one
#~ plotPressure(pmin,pmax,dp,Tmin,Tmax,dT)

plt.show()
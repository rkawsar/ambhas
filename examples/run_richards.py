# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 10:47:16 2012

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""
from ambhas.richards import RICHARDS_1D
import matplotlib.pyplot as plt
from scipy.io import netcdf as nc

params = {'axes.labelsize': 15, 
          'text.fontsize': 15,
          'legend.fontsize': 15,
          'xtick.labelsize': 15,
          'ytick.labelsize': 15,
          'text.usetex': False}
plt.rcParams.update(params)

maddur = RICHARDS_1D('/home/tomer/svn/ambhas/examples/maddur.xls')
output_file = nc.NetCDFFile(maddur.ofile_name, 'r')

theta = output_file.variables['sm'][:]
doy = range(1,367)
rain = output_file.variables['rain'][:]



# main plot
plt.close()
fig = plt.figure(figsize=(6, 4.5))
ax = plt.axes([0.15, 0.15, 0.7, 0.7])
ax.plot(doy,theta[0,:],'b')
ax.plot(doy,theta[20,:],'g')
ax.plot(doy,theta[39,:],'c')
ax.set_ylabel('Soil Moisture (v/v)')
ax.set_ylim(ymax=0.4)
ax.set_xlim(xmax=366)
ax.set_xlabel('DOY')
fig.canvas.draw()
	
# precipitation plot
ax2 = plt.twinx()
ax2.bar(doy,rain*86400*1000, label='Precipitation', color='m', edgecolor='m')
ax2.set_ylabel('Precipitation (mm)')
ax2.set_ylim(ymax=100)
ax2.set_xlim(xmax=366)
ax2.invert_yaxis()

p1 = plt.Rectangle((0, 0), 1, 1, fc="m")
p2 = plt.Rectangle((0, 0), 1, 1, fc="b")
p3 = plt.Rectangle((0, 0), 1, 1, fc="g")
p4 = plt.Rectangle((0, 0), 1, 1, fc="c")
leg = plt.legend([p1,p2,p3,p4], ["Precipitation","SM at surface", "SM at 1m", "SM at 2m"], loc=(0.01,0.4))
frame = leg.get_frame()
frame.set_alpha(0.5)

plt.savefig('/home/tomer/svn/ambhas-wiki/images/run_richards.png')



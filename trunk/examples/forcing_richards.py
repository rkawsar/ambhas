# -*- coding: utf-8 -*-
"""
Created on Sun Nov 11 11:53:27 2012

@author: Sat kumar tomer
@website: www.ambhas.com

this scripts plots the forcing for the richards' input file
"""

import numpy as np
import matplotlib.pyplot as plt
from ambhas.xls import xlsread

in_file = 'maddur.xls'
xls_file = xlsread(in_file)
doy = xls_file.get_cells('B2:B366','forcing')
rain = xls_file.get_cells('C2:C366','forcing')
pet = xls_file.get_cells('D2:D366','forcing')

plt.clf()
plt.bar(doy,rain, color='m', edgecolor='m', label='Rainfall')
plt.plot(pet, label='PET')
plt.grid(True)
plt.legend()
plt.xlabel('DOY')
plt.ylabel('mm')
plt.savefig('output/richards_forcing.png')

#from ambhas.richards import RICHARDS_1D


#maddur = RICHARDS_1D('/home/tomer/richards/input/maddur.xls')
#output_file = nc.NetCDFFile(maddur.ofile_name, 'r')
#print output_file.variables
#foo = output_file.variables['sm']
#theta= foo.getValue()
#print theta[:,-2]
#print theta[:,-1]
#plt.plot(theta[:,-1]); plt.plot(theta[:,-2]); plt.show()
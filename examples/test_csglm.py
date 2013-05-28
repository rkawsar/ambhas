# -*- coding: utf-8 -*-
"""
Created on Thu Jan  5 19:05:00 2012

@author: Sat Kumar Tomer
@website: www.ambhas.com
@email: satkumartomer@gmail.com
"""


# import required modules
import numpy as np
import xlrd
import os
from gdalconst import *
from scipy.interpolate import Rbf
from Scientific.IO import NetCDF as nc

/home/tomer/svn/ambhas/examples/berambadi.xls

# generate synthetic data
t = 100
rainfall = np.random.rand(t)
pet = np.random.rand(t)
lai = np.random.rand(t)
no_layer = 5
root_frac = np.random.rand(no_layer)
z = np.random.rand(no_layer)

soil_par = {}
soil_par['qr'] = np.random.rand(no_layer)
soil_par['f'] =  np.random.rand(no_layer)
soil_par['a'] =  np.random.rand(no_layer)
soil_par['n'] =  np.random.rand(no_layer)
soil_par['Ks'] =  np.random.rand(no_layer)
soil_par['l'] =  np.random.rand(no_layer)
soil_par['evap_0'] =  np.random.rand(1)
soil_par['evap_1'] = np.random.rand(1)

runoff_par = np.random.rand(2)
gw_par = np.random.rand(2)






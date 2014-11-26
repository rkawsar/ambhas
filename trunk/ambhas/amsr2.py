#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 11:30:24 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

import numpy as np
import h5py
import os
import datetime as dt

def extract_smc(h5_file, lat, lon):
    """
    Extract Soil Moisture Content from AMSR2 h5 products
    Input:
        h5_file: a single file name
        lat: latitude, either a single value or min,max limits
             eg. 
             lat = 12
             lat = [10,15] 
        lon: longitude, either a single value or min,max limits
             eg. as for lat
    """
    res = 0.1
    ######### convert lat, lon into indices ##############
    # min max are given    
    min_max = type(lat) is list
    if min_max:
        lat_min = lat[0]
        lat_max = lat[1]
        i_lat_min = int(np.floor((90-lat_min)/res))
        i_lat_max = int(np.floor((90-lat_max)/res))
        lon_min = lon[0]
        lon_max = lon[1]
        if lon_min<0: lon_min += 360
        if lon_max<0: lon_max += 360
        j_lon_min = int(np.floor(lon_min/res))
        j_lon_max = int(np.floor(lon_max/res))
    else: # if only single value of lat, lon is given
        i_lat = np.floor((90-lat)/res)
        i_lat = i_lat.astype(int)
        lon1 = np.copy(lon)
        if lon1<0:
            lon1 += 360
        j_lon = np.floor(lon1/res)
        j_lon = j_lon.astype(int)   
    
    # read the data
    if type(h5_file) is str:
        f = h5py.File(h5_file,  "r")
        if min_max:
            smc = f["Geophysical Data"][i_lat_max:i_lat_min+1, j_lon_min:j_lon_max+1,0]
        else:
            smc = f["Geophysical Data"][i_lat, j_lon,0]
    elif type(h5_file) is list:
        n = len(h5_file)
        if min_max:
            nlat = i_lat_min+1 - i_lat_max
            nlon = j_lon_max+1 - j_lon_min
            smc = np.empty((n, nlat, nlon))
            for h5_f,i in zip(h5_file, range(n)):
                f = h5py.File(h5_f,  "r")
                smc[i,:,:] = f["Geophysical Data"][i_lat_max:i_lat_min+1, j_lon_min:j_lon_max+1,0]
                f.close()
            
        else:
            smc = np.empty(n,)
            for h5_f,i in zip(h5_file, range(n)):
                f = h5py.File(h5_f,  "r")
                smc[i] = f["Geophysical Data"][i_lat, j_lon,0]
                f.close()
    
    try:
        smc[smc<0] = np.nan
    except:
        if smc <0: smc = np.nan
      
    return smc

def extract_dates(h5_file):
    h5_dates = []
    for h5_f in h5_file:
        foo = os.path.basename(h5_f)[7:15]
        h5_dates.append(dt.datetime.strptime(foo, '%Y%m%d'))
    return h5_dates

def extract_orbit(h5_file):
    asc = []
    for h5_f in h5_file:
        f = h5py.File(h5_f,  "r")
        if f.attrs['OrbitDirection'][0] == 'Ascending':
            asc.append(True)
        elif f.attrs['OrbitDirection'][0] == 'Descending':
            asc.append(False)
        else:
            asc.append(None)
        f.close()
    return asc



if __name__ == "__main__":
    import glob
    h5_file = '/home/tomer/amsr2/data/h5/GW1AM2_20130722_01D_EQMD_L3SGSMCHA1100100.h5'
    h5_file = glob.glob('/home/tomer/amsr2/data/h5/GW1AM2_201?????_01D*.h5')
    h5_file.sort()
    h5_file = h5_file[:5]
    lat = [8, 38]
    lon = [68, 98]
    sm = extract_smc(h5_file, lat, lon)
    sm_dates = extract_dates(h5_file)
    asc = extract_orbit(h5_file)
    
    
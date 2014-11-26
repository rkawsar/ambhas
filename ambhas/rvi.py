#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 16:58:55 2014

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com
"""

from __future__ import division

from osgeo.gdalconst import *
from osgeo import gdal
import glob
import os


def compute_rvi(bc_dir, rvi_dir):
    """
    bc_dir: directory of the bc file
    list
    
    rvi_dir: directory to store the rvi files
    """
    
    bc_files = glob.glob(os.path.join(bc_dir, '*.tif'))
    
    for bc_file in bc_files:
        rvi_file = os.path.join(rvi_dir, os.path.basename(bc_file))
        print rvi_file
        # read the data
        dataset = gdal.Open(bc_file, GA_ReadOnly)
        
        geotransform = dataset.GetGeoTransform()
        gcps = dataset.GetGCPs()
        gcpproj = dataset.GetGCPProjection()
        RasterXSize = dataset.RasterXSize
        RasterYSize = dataset.RasterYSize    
        
        HH = dataset.GetRasterBand(1).ReadAsArray()
        HV = dataset.GetRasterBand(2).ReadAsArray()
        VH = dataset.GetRasterBand(3).ReadAsArray()
        VV = dataset.GetRasterBand(4).ReadAsArray()
        dataset = None
        
        # compute rvi
        HH /= 10
        HV /= 10
        VH /= 10
        VV /= 10
    
        HH = 10**HH
        HV = 10**HV
        VH = 10**VH
        VV = 10**VV
    
        rvi = 8*HV/(HH+VV+2*HV)
        # rvi>1.5 comes at the place of missing data, hence replace by nan
        rvi[rvi>1.5] = np.nan
    
        # save the data as Geotiff
        driver = gdal.GetDriverByName('GTiff')
        output_dataset = driver.Create(rvi_file, RasterXSize, RasterYSize,1,gdal.GDT_Float32)
        output_dataset.SetGeoTransform(geotransform)
        output_dataset.SetGCPs(gcps, gcpproj)
        output_dataset.GetRasterBand(1).WriteArray(rvi, 0, 0)
        output_dataset = None
        
        print('%s is done'%bc_file)


    

if __name__ == '__main__':
    bc_dir = '/home/tomers/radarsat_2014/bc_20m/'
    rvi_dir = '/home/tomers/radarsat_2014/rvi_20m'
    compute_rvi(bc_dir, rvi_dir)
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 10:29:02 2012

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com


This scripts converts the raw risat data into backscatter coefficient
the script is only for the utm 43 zone,
some modification woould be need for other utm zones
"""

from osgeo import gdal
from osgeo.gdalconst import *
import matplotlib.pyplot as plt
from ambhas.gis import utm2deg, deg2utm,Pixel2Geo
import numpy as np
from xml.dom import minidom
from xml.dom.minidom import parseString
from scipy.signal import medfilt2d, wiener

def speckle_filter(ifile, ofile):
    """
    ifile
    ofile
    """
    # read the Digital Number (DNp)
    dataset = gdal.Open(ifile,GA_ReadOnly)
    sigma = dataset.GetRasterBand(1).ReadAsArray()
    inci = dataset.GetRasterBand(2).ReadAsArray()
    RasterXSize = dataset.RasterXSize
    RasterYSize = dataset.RasterYSize
    GT = dataset.GetGeoTransform()
    projection = dataset.GetProjection()
    dataset = None
    
    # filter
    sigma = medfilt2d(sigma, kernel_size=7)
    #sigma = wiener(sigma, mysize=(7,7),noise=None)
    
    # same as geotiff
    driver = gdal.GetDriverByName('GTiff')
    output_dataset = driver.Create(ofile, RasterXSize, RasterYSize,2,gdal.GDT_Float32)
    output_dataset.SetGeoTransform(GT)
    output_dataset.SetProjection(projection)
    output_dataset.GetRasterBand(1).WriteArray(sigma, 0, 0)
    output_dataset.GetRasterBand(2).WriteArray(inci, 0, 0)
    output_dataset = None


def raw_bc(risat_dir, risat_file, grid_file, out_file):
    """
    Input:
        risat_dir
        risat_file
        out_file
    """
    
    xml_file = risat_dir + 'product.xml'
    band_meta_file = risat_dir + 'BAND_META.txt'
    grid_file = risat_dir + grid_file 
   
    
    # read the Digital Number (DNp)
    dataset = gdal.Open(risat_dir+risat_file,GA_ReadOnly)
    DN = dataset.GetRasterBand(1).ReadAsArray()
    RasterXSize = dataset.RasterXSize
    RasterYSize = dataset.RasterYSize
    GT = dataset.GetGeoTransform()
    projection = dataset.GetProjection()
    dataset = None
    DN = DN.astype(np.float32)
    DN[DN<=0] = np.nan
    DN[DN>1e10] = np.nan
    
    # read the Calibration Constant (KdB)
    file = open(xml_file,'r')
    data = file.read()
    file.close()
    dom = parseString(data)
    foo1 = dom.getElementsByTagName('calibrationConstant')[0].toxml()
    foo2 = dom.getElementsByTagName('calibrationConstant')[1].toxml()
    if "HH" in foo1:
        Kdb = dom.getElementsByTagName('calibrationConstant')[0].firstChild.data
    elif "HH" in foo2:
        Kdb = dom.getElementsByTagName('calibrationConstant')[1].firstChild.data
    Kdb = np.float(Kdb)

    # read incidence angle and satellite pass date
    f = open(band_meta_file, 'r')
    for line in f:
        # do things with your file
        foo = line.split('=')
        if foo[0]=="IncidenceAngle":
            i_center = float(foo[1])
        elif foo[0]=="DateOfPass":
            DateOfPass = str(foo[1])
    f.close()
    
    # make the name of output file using hte DateOfPass
        
    f = open(grid_file, 'r')

    # Read and ignore header lines
    header1 = f.readline()
    header2 = f.readline()
    header3 = f.readline()
    header4 = f.readline()
    header5 = f.readline()

    foo = header1.strip()
    row = int(header1.split()[-1])
    foo = header2.strip()
    col = int(header2.split()[-1])


    # Loop over lines and extract variables of interest
    lat = []
    lon = []
    inci = []
    for line in f:
        line = line.strip()
        columns = line.split()
        lat.append(float(columns[0]))
        lon.append(float(columns[1]))
        inci.append(float(columns[3])) 

    f.close()
    lat = np.array(lat)
    lon = np.array(lon)
    inci = np.array(inci)
    inci[inci<0] = np.nan
    
    lat = lat[~np.isnan(inci)]
    lon = lon[~np.isnan(inci)]
    inci = inci[~np.isnan(inci)]
    
    x,y = deg2utm(lon,lat)

    xx = np.empty((len(lat),6))
    xx[:,0] = 1
    xx[:,1] = x
    xx[:,2] = y
    xx[:,3] = x**2
    xx[:,4] = y**2
    xx[:,5] = x*y
    
    be = np.linalg.lstsq(xx,inci)[0]

    row_n, col_n = DN.shape
    X, Y = np.meshgrid(np.arange(col_n), np.arange(row_n))
    
    Xgeo,Ygeo = Pixel2Geo(X,Y,GT)
    Inci = be[0] + be[1]*Xgeo + be[2]*Ygeo + be[3]*Xgeo**2 + be[4]*Ygeo**2 + be[5]*Xgeo*Ygeo
    
    sigma = 20*np.log10(DN)-Kdb + 10*np.log10(np.sin(Inci*np.pi/180.0)/np.sin(i_center*np.pi/180.0))
    
    sigma[sigma>10] = 10
    sigma[sigma<-25] = -25

    # save as geotiff
    driver = gdal.GetDriverByName('GTiff')
    output_dataset = driver.Create(out_file, RasterXSize, RasterYSize,2,gdal.GDT_Float32)
    output_dataset.SetGeoTransform(GT)
    output_dataset.SetProjection(projection)
    output_dataset.GetRasterBand(1).WriteArray(sigma, 0, 0)
    output_dataset.GetRasterBand(2).WriteArray(Inci, 0, 0)
    output_dataset = None




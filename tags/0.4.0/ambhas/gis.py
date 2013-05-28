#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 15 19:54:08 2010

@author: sat kumar tomer (http://civil.iisc.ernet.in/~satkumar/)

Functions:
    utm2deg: Calculate utm co-ordinates from Lat, Lon
    deg2utm : Calculate Lat, Lon from UTM
    kabini: 
    berambadi: 
    great_circle_distance:
        
"""

# load needed python modules 
from pyproj import Proj
import os
from subprocess import call
import sys
import numpy as np
import matplotlib.pyplot as plt

def utm2image(GT,utm):
    Xpixel = ((utm[:,0] - GT[0])*GT[5] - (utm[:,1] - GT[3])*GT[2])/(GT[1]*GT[5]-GT[4]*GT[2])
    Ypixel = ((utm[:,1] - GT[3])*GT[1] - (utm[:,0] - GT[0])*GT[4])/(GT[1]*GT[5]-GT[4]*GT[2])
    return (np.round(Xpixel)).astype('int'),(np.round(Ypixel)).astype('int')

def Geo2Pixel(Xgeo,Ygeo,GT):
    a1 = GT[1]
    b1 = GT[2]
    c1 = Xgeo - GT[0]
    a2 = GT[4]
    b2 = GT[5]
    c2 = Ygeo - GT[3]
    Xpixel = (b2*c1-b1*c2)/(a1*b2-a2*b1) 
    Yline = (a2*c1-a1*c2)/(a2*b1-a1*b2) 
    return Xpixel, Yline

def Pixel2Geo(Xpixel,Yline,GT):
    Xgeo = GT[0] + Xpixel*GT[1] + Yline*GT[2]
    Ygeo = GT[3] + Xpixel*GT[4] + Yline*GT[5]
    return Xgeo,Ygeo

def SetProjectionBerambadi():
	return 'PROJCS["WGS 84 / UTM zone 43N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",75],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","32643"]]'

def utm2deg(x,y,utmzone=43):
    p = Proj(proj='utm',zone=43,ellps='WGS84')
    Lon,Lat = p(x, y, inverse=True)
    return Lon,Lat
    
def deg2utm(Lon,Lat,utmzone=43):
    p = Proj(proj='utm',zone=utmzone,ellps='WGS84')
    x,y = p(Lon, Lat)
    return x,y
    
def kabini(Ifile,Ofile):
    # define the file names file
    Temp1 = '/home/tomer/MODISdata/temp/temp1.tif'
    Temp2 = '/home/tomer/MODISdata/temp/temp2.tif'
            
    # convert from geographical co-ordinates to UTM zone 43
    cmd= 'gdalwarp -r bilinear -t_srs  \'+proj=utm +zone=43 +datum=WGS84\' ' + Ifile + ' ' +Temp1
    try:
        returncode = call(cmd, shell=True)
        if returncode:
            print 'Failure with returncode', returncode; sys.exit(1)
    except OSError, message:
        print 'Execution failed!\n', message; sys.exit(1)

    # cut the area around Kabini Basin (output image will be of size 129 X 102)
    kab='582000 1372000 711000 1270000'
    cmd = 'gdal_translate -a_ullr ' + kab + ' -projwin ' + kab + ' ' + Temp1+ ' ' + Temp2
    try:
        returncode = call(cmd, shell=True)
        if returncode:
            print 'Failure with returncode', returncode; sys.exit(1)
    except OSError, message:
        print 'Execution failed!\n', message; sys.exit(1)
        
    # changing the resolution
    cmd = 'gdalwarp -r bilinear -tr 1000 1000 ' + Temp2 + ' ' +Ofile
    try:
        returncode = call(cmd, shell=True)
        if returncode:
            print 'Failure with returncode', returncode; sys.exit(1)
    except OSError, message:
        print 'Execution failed!\n', message; sys.exit(1)
        
    # remove the temporary file
    try:
        os.remove(Temp)
        os.remove(Temp2)
    except:
        print 'temp file not created'

def berambadi(Ifile,Ofile):
    # define the file names file
    Temp1 = '/home/tomer/MODISdata/temp/temp1.tif'
    Temp2 = '/home/tomer/MODISdata/temp/temp2.tif'
            
    # convert from geographical co-ordinates to UTM zone 43
    cmd= 'gdalwarp -r bilinear -t_srs  \'+proj=utm +zone=43 +datum=WGS84\' ' + Ifile + ' ' +Temp1
    try:
        returncode = call(cmd, shell=True)
        if returncode:
            print 'Failure with returncode', returncode; sys.exit(1)
    except OSError, message:
        print 'Execution failed!\n', message; sys.exit(1)

    # cut the area around Kabini Basin (output image will be of size 129 X 102)
    bmd='664000 1309000 685000 1294000'
    cmd = 'gdal_translate -a_ullr ' + bmd + ' -projwin ' + bmd + ' ' + Temp1+ ' ' + Temp2
    try:
        returncode = call(cmd, shell=True)
        if returncode:
            print 'Failure with returncode', returncode; sys.exit(1)
    except OSError, message:
        print 'Execution failed!\n', message; sys.exit(1)
        
    # changing the resolution
    cmd = 'gdalwarp -r bilinear -tr 1000 1000 ' + Temp2 + ' ' +Ofile
    try:
        returncode = call(cmd, shell=True)
        if returncode:
            print 'Failure with returncode', returncode; sys.exit(1)
    except OSError, message:
        print 'Execution failed!\n', message; sys.exit(1)
        
    # remove the temporary file
    try:
        os.remove(Temp1)
        os.remove(Temp2)
    except:
        print 'temp file not created'
        
 
def geodetic_area(lon_cen, size_cell):
    """
    Compute the area in square meters given the longitude of the 
    center and size of the grid 
    
    The grid should be square in terms of degree i.e. the size of the 
    cell should not vary in latitude and longitude
    
    input:
        lon_cen: longitude of the center of grid
        size_cell: size of the cell in the degree
        
    output:
        area: area of the square grid
    """
    r = 6371229.0 # radius of earth in meters
    area = r**2*np.abs(size_cell)*np.pi/180*np.abs(
    			np.sin((lon_cen-size_cell/2.0)*np.pi/180) - \
			np.sin((lon_cen+size_cell/2.0)*np.pi/180))
    return area


def latitude_length(longitude):
    """
    computes the length of one degree of a latitude
    """
    a = 6378137.0
    b = 6356752.3142
    e = np.sqrt((a**2 - b**2)/a**2)
    length = np.pi*a*(1-e**2)/(180*(1-e**2*np.sin(longitude*np.pi/180.0)**2)**1.5)
    return length

def longitude_length(longitude):
    """
    computes the length of one degree of a longitude
    """
    a = 6378137.0
    b = 6356752.3142
    e = np.sqrt((a**2 - b**2)/a**2)
    length = np.pi*a*np.cos(longitude*np.pi/180)/(180*(1-e**2*np.sin(longitude*np.pi/180.0)**2)**0.5)
    return length

def great_circle_distance(lat_s,lon_s,lat_f,lon_f):
    """
    computes the great circle distance between two points
    Input:
        lat_s : latitute (degree) of the standpoint
        lon_s : longitude (degree) of the standpoint
        lat_f : latitute (degree) of the forepoint
        lon_f : longitude (degree) of the forepoint
    Output:
        dis: great circle distance (km)
    """
    r = 6372.8
    phi_f = lat_f*np.pi/180.0
    phi_s = lat_s*np.pi/180.0
    dl =  np.abs(lon_f-lon_s)*np.pi/180.0
    foo1 = np.sqrt((np.cos(phi_f)*np.sin(dl))**2 + (np.cos(phi_s)*np.sin(phi_f) - np.sin(phi_s)*np.cos(phi_f)*np.cos(dl))**2 )
    foo2 = np.sin(phi_s)*np.sin(phi_f) + np.cos(phi_s)*np.cos(phi_f)*np.cos(dl)
    
    dis = r*np.arctan2(foo1,foo2)
    return dis    

def read_ascii_grid(fname, dtype='float'):
    """
    A function to read the ascii grid data		
    
    Input:
        fname:	input file name
    """
    # open file for reading
    f = open(fname, 'r')
    
    # read the header information
    var = ['nrows', 'ncols', 'xllcorner', 'yllcorner', 'cellsize', 
           	'NODATA_value']
            
    for i in range(6):
        foo = f.readline().split()
        exec("%s = %s"%(foo[0],foo[1]))
    
    # check if all the variables are read
    # if not then issue an error
    header = {}
    for v in var:
        try:
            exec("header['%s'] = %s"%(v,v)) 
        except NameError:
            print "The variable %s could not be find in the file"%v
    f.close()
    
    data = np.genfromtxt(fname, skip_header=6, dtype = dtype)	
    data[data==NODATA_value] = np.nan		
    
    return data, header
		

def write_ascii_grid(fname, data, header, dtype='float'):
    """
    A function to write the ascii grid data		
        Input:
            fname:	input file name
            data:	input data 
            header information:	nrows ncols xllcorner yllcorner cellsize NODATA_value
            dtype: 	data type of the data variable
    """
    # convert the data type
    data = data.astype(dtype)
    
    # open file for reading
    f = open(fname, 'w')
    
    # write the header information
    var = ['nrows', 'ncols', 'xllcorner', 'yllcorner', 'cellsize', 
           	'NODATA_value']
    
    # check if all the variables are read
    # if not then issue an error
    for v in var:
        try:
            exec("header['%s']"%v)
        except NameError:
            print "The variable %s could not be find in the file"%v
            
    for i in range(6):
        f.write('%s \t %s \n'%(var[i],header[var[i]]))
        
    # convert the nan into NODATA_value
    data[np.isnan(data)] = header['NODATA_value']
    
    # write the data
    for i in range(header['nrows']):
        for j in range(header['ncols']):
            f.write('%s '%data[i,j])
        f.write('\n'%data[i,j])
    f.close()
    
    return 0

if __name__ == '__main__':
    # from utm to degree
    x = 60000
    y = 1200000
    lat,lon = utm2deg(x,y,utmzone=43)
    print(lat,lon)
    # from degree to utm
    x,y = deg2utm(lat,lon,utmzone=43)
    
    print(x,y)
 

    # test the sample 
    fname = '/home/tomer/svn/ambhas/examples/sample_ascii_grid.grd'
    data, header = read_ascii_grid(fname)
    print data    
    print header
    
    #plt.matshow(data)
    #plt.show()
    
    # write the sample
    fname = '/home/tomer/svn/ambhas/examples/sample_ascii_grid_out.grd'
    write_ascii_grid(fname, data, header)
    
    #generate the area of the square grid globally with 1 degree resolution
    #lon_cen = np.linspace(-90,90)
    #size = 1
    
    #area = geodetic_area(lon_cen, size)
    #area1 = geodetic_area(lon_cen, size/1.0)
    
    #plt.plot(lon_cen, area1/1e6)
    #plt.xlabel('Longitude (degree)')
    #plt.ylabel('Area of a degree square (Sq. km)')
    #plt.show()
    
    # length of latitude and longitude
    #longitude = np.linspace(0,90)
    #len_lat = latitude_length(longitude)
    #len_lon = longitude_length(longitude)
    
    #ax1 = plt.subplot(111)
    #plt.plot(latitude, len_lat/1000, 'b-', label='Latitude')
    #ax1.set_xlabel('Longitude (degree)')
    #ax1.set_ylabel('Length of a degree Latitude (km)', color='b')
    #for tl in ax1.get_yticklabels():
        #	tl.set_color('b')
    
    #ax2 = plt.twinx()
    #ax2.plot(latitude, len_lon/1000, 'r--')
    #for tl in ax2.get_yticklabels():
        #	tl.set_color('r')
    #ax2.set_ylabel('Length of a degree Longitude (km)', color='r')
    #plt.show()
    
    ## great circle distance example
    lat_s, lon_s = 36.12, -86.67
    lat_f, lon_f = 33.94, -118.40
    dis = great_circle_distance(lat_s,lon_s,lat_f,lon_f)
	
	

# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 19:18:08 2012

@author: Sat Kumar Tomer
@website: www.ambhas.com
@email: satkumartomer@gmail.com
"""

# import required libraries
from osgeo.gdalconst import *
import gdal, xlrd,xlwt
import numpy as np

ds = ['/home/tomer/soil_map/raster/theta_r.tif', 
      '/home/tomer/soil_map/raster/theta_s.tif']
ds_short_name = ['theta_r', 'theta_s']
xls_out = '/home/tomer/out.xls'

def extract_gis(xls_in, xls_out, ds, ds_short_name):
    """
    it reads the gis file defined in the ds
    then extract the data at coordinates defined in each sheet of the xls_in file
    and then write the data in the xls_out file
    the header of the data in the xls_out are written as defined in the 
    ds_short_name
    
    xls_in: the name of the input xls file containing the co-ordinates of the plot
    xls_out: the xls file in which the output will be written
    ds: the data source file name in the gis format, these files must be in the 
        tiff format
    ds_short_name:  the name the will appear as header in the output xls file
    """
    
    if type(ds) is not list:
        raise TypeError('input ds should be of list type')
    
    book_out = xlwt.Workbook()

    final_data = np.empty((66,2,len(ds)))
    for k in range(len(ds)):
        dataset = gdal.Open(ds[k], GA_ReadOnly)
        data = dataset.GetRasterBand(1).ReadAsArray() 
        GT = dataset.GetGeoTransform()
        
        book = xlrd.open_workbook('plots_66.xls')
        
        for i in xrange(66):
            sheet = book.sheet_by_name(str(i+1))
            xy = np.empty((sheet.nrows-1,2))
            for j in range(xy.shape[0]):
                xy[j,0] = sheet.cell_value(j+1,0)    
                xy[j,1] = sheet.cell_value(j+1,1)
                    
            x,y = utm2image(GT,xy)
                
            extracted_data = data[y,x]
            final_data[i,0,k] = np.median(extracted_data)
            final_data[i,1,k] = np.std(extracted_data)
    
    dataset = None
    
    sheet_median = book_out.add_sheet('median')   
    sheet_std = book_out.add_sheet('std')
    
    sheet_median.write(0,0,'Plot no.')
    sheet_std.write(0,0,'Plot no.')
    
    for i in range(final_data.shape[0]):
        sheet_median.write(i+1,0,i+1)
        sheet_std.write(i+1,0,i+1)
    
    for i in range(len(ds)):
        sheet_median.write(0,i+1,ds_short_name[i])
        sheet_std.write(0,i+1,ds_short_name[i])
    
    for i in range(final_data.shape[0]):
        for j in range(final_data.shape[2]):
            sheet_median.write(i+1, j+1, final_data[i,0,j])
            sheet_std.write(i+1, j+1, final_data[i,1,j])
    book_out.save(xls_out)
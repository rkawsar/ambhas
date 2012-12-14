# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 19:18:08 2012

@author: Sat Kumar Tomer
@website: www.ambhas.com
@email: satkumartomer@gmail.com
"""

# import required libraries
from osgeo.gdalconst import *
import gdal, xlrd, xlwt
import numpy as np
from ambhas.gis import utm2image
import matplotlib.nxutils as nx
from ambhas.xls import xlsread

def extract_gis(xls_in, xls_out, ds, ds_short_name, band=1, n=66):
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
    ds_short_name:  the name that will appear as header in the output xls file
    band: band of the raster data to extract
    """
    
    if type(ds) is not list:
        raise TypeError('input ds should be of list type')
    
    book_out = xlwt.Workbook()

    final_data = np.empty((n,2,len(ds)))
    for k in range(len(ds)):
        dataset = gdal.Open(ds[k], GA_ReadOnly)
        data = dataset.GetRasterBand(band).ReadAsArray() 
        GT = dataset.GetGeoTransform()
        
        book = xlrd.open_workbook(xls_in)
        
        for i in xrange(n):
            sheet = book.sheet_by_name(str(i+1))
            xy = np.empty((sheet.nrows-1,2))
            for j in range(xy.shape[0]):
                xy[j,0] = sheet.cell_value(j+1,0)    
                xy[j,1] = sheet.cell_value(j+1,1)
                    
            x,y = utm2image(GT,xy)
                
            extracted_data = data[y,x]
            final_data[i,0,k] = np.median(extracted_data)
            final_data[i,1,k] = np.std(extracted_data)
            
        print('%i/%i'%(k+1,len(ds)))
    
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


def corner_to_grid(xls_in, xls_out, in_sheet='Sheet1', res=5, rows=(2,67)):
    """
    it reads the xls file defined in the xls_in
    take the corner of the monitoring plots 
    make a grid of res m resolution
    and save the output in xls_out
    
    this xls_out file can be used by ambhas.extract_gis_data.extract_gis function
    to extract the data over monitoring plots
    
    Note that there should be only and only 4 corner points defined for the plots
    
    Input:
        xls_in: name of xls input file
        xls_out: name of xls output file
        in_sheet: name of the sheet to be read from xls input file, default(Sheet1)
        res: resolution of the output grid in meters, default(5)
        rows: a tuple indicating the beginning and end of rows to read from
                input xls file, e.g. (2,67)
    """
    
    xls_file = xlsread(xls_in)
    xy = xls_file.get_cells('B%i:I%i'%(rows[0],rows[1]), in_sheet)
    
    # writting output to excel file
    book = xlwt.Workbook()
    
    for i in xrange(xy.shape[0]):
    
        sheet = book.add_sheet(str(i+1))    
        
        verts = xy[i,:].reshape(4,2)
        min_x = verts.min(axis=0)[0]
        max_x = verts.max(axis=0)[0]
        min_y = verts.min(axis=0)[1]
        max_y = verts.max(axis=0)[1]
        
        min_x = min_x - np.mod(min_x,res)
        min_y = min_y - np.mod(min_y,res)
        max_x = max_x - np.mod(max_x,res)+res
        max_y = max_y - np.mod(max_y,res)+res
        
        x = np.arange(min_x, max_x, res) 
        y = np.arange(min_y, max_y, res)
        
        X,Y = np.meshgrid(x,y)
        
        points = np.vstack([X.flatten(), Y.flatten()]).T
        
        foo = nx.points_inside_poly(points, verts)
        
        
        sheet.write(0,0,'x')
        sheet.write(0,1,'y')
        
        for j in xrange(foo.sum()):
            sheet.write(j+1,0,points[foo,0][j])
            sheet.write(j+1,1,points[foo,1][j])
        
        print("%i/%i"%(i+1,xy.shape[0]))
    
    book.save(xls_out) 

if __name__=='__main__':
    # example for corner_to_grid
    xls_in = '/home/tomer/surface_sm/raw_data/locations.xls'    
    xls_out = '/home/tomer/temp/temp.xls'
    corner_to_grid(xls_in, xls_out, in_sheet='utm')
    
    
    
    
# -*- coding: utf-8 -*-
"""
Created on Tue May  7 12:57:49 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""
import numpy as np
from osgeo.gdalconst import *
from osgeo import gdal

from ambhas.dubois import inverse_dubois
from ambhas.oh1992 import inverse_oh1992
from ambhas.oh1994 import inverse_oh1994
from ambhas.oh2002 import inverse_oh2002
from ambhas.oh2004 import inverse_oh2004
from ambhas.progress_bar import PB


class inverse_radar:
    
    def __init__(self, hh, hv, vh, vv, ia, wl):
        """
        class for retrieving the soil moisture from the 
        Dubois, Oh1992, Oh1994, Oh2002 and Oh2004 models
        
        Input:
            hh: (dB) a float or an array
            hv: (dB) a float or an array
            vh: (dB) a float or an array
            vv: (dB) a float or an array
            ia: incidence angle (degree) (a float or an array), if it is constant for
                all the data, then only a single value can be specified
            wl: wavelength (cm) (a float or an array), if it is constant for
                all the data, then only a single value can be specified
        """
        hh = np.array(hh)
        vh = np.array(vh)
        hv = np.array(hv)
        vv = np.array(vv)
        
        orig_shape = hh.shape # original shape of the input arrays
        
        # if ia or wl is single value, make it an array of same size as of hh
        ia = np.array([ia])
        wl = np.array([wl])
        if len(ia) == 1:
            ia = np.ones(orig_shape)*ia
        if len(wl) == 1:
            wl = np.ones(orig_shape)*wl
                
        # flatten the arrays, and store the np.unravel_index
        self.hh = hh.flatten()
        self.hv = hv.flatten()
        self.vh = vh.flatten()
        self.vv = vv.flatten()
        self.ia = ia.flatten()
        self.wl = wl.flatten()
        self.n = len(self.hh)
        self.orig_shape = orig_shape
        self.k = 2*np.pi/self.wl # wave number
        
        # mask for (vegetation) and (soil roughness)
        temp = np.zeros(self.n)
        self.mask = (temp!=0)
        
        self._vegetation_mask()
        self._soil_rough_mask()
        
    def _vegetation_mask(self):
        """
        mask for the too heavily vegetation (Dubois, 1995)
        """
        self.mask[(self.hv-self.vv)>-11] = True
    
    def _soil_rough_mask(self):
        """
        mask for the soil roughness (Oh, 1992)
        """
        self.mask[(self.hh-self.vv)>0] = True
    
    def retrieve_dubois(self):
        """
        Retrieve soil moisture using the Dubois model
        Output:
            mv: soil moisture (v/v)
            h: soil roughness (cm)
            dubois_range: 
        """
        hh = self.hh
        vv = self.vv
        theta = self.ia
        wl = self.wl
        
        mv = np.empty(self.n)
        h = np.empty(self.n)
        for i in xrange(self.n):
            if self.mask[i]:
                mv[i], h[i] = np.nan, np.nan
            else:
                mv[i], h[i] = inverse_dubois(hh[i], vv[i], theta[i], wl[i])

        self.dubois_range = {'max_kh':2.5, 'max_mv':0.35, 'min_theta':30}           
        
        mv.shape = self.orig_shape
        h.shape = self.orig_shape
        return mv, h
    
    def retrieve_oh1992(self):
        """
        Retrieve soil moisture using the Oh(1992) model
        Output:
            mv: soil moisture (v/v)
            h: soil roughness (cm)
        """
        hh = self.hh
        vv = self.vv
        hv = self.hv
        theta = self.ia
        wl = self.wl

        p = hh-vv
        q = hv-vv        
        
        mv = np.empty(self.n)
        ks = np.empty(self.n)
        for i in xrange(self.n):
            if self.mask[i]:
                mv[i], ks[i] = np.nan, np.nan
            else:
                mv[i], ks[i] = inverse_oh1994(p[i], q[i], theta[i])

        k = 2*np.pi/wl
        h = ks/k        
        
        self.oh1992_range = {'min_kh':0.1, 'max_kh':6.0, 'min_kl':2.6, 
                             'max_kl':19.7, 'min_mv':0.09, 'max_mv':0.31}     
        
        mv.shape = self.orig_shape
        h.shape = self.orig_shape
        return mv, h
    
    def retrieve_oh1994(self):
        """
        Retrieve soil moisture using the Oh(1994) model
        Output:
            mv: soil moisture (v/v)
            h: soil roughness (cm)
        """
        hh = self.hh
        vv = self.vv
        hv = self.hv
        theta = self.ia
        wl = self.wl

        p = hh-vv
        q = hv-vv        
        
        mv = np.empty(self.n)
        ks = np.empty(self.n)
        for i in xrange(self.n):
            if self.mask[i]:
                mv[i], ks[i] = np.nan, np.nan
            else:
                mv[i], ks[i] = inverse_oh1992(p[i], q[i], theta[i])

        k = 2*np.pi/wl
        h = ks/k        
        
        mv.shape = self.orig_shape
        h.shape = self.orig_shape
        
        return mv, h    

    def retrieve_oh2002(self, output_rough_length=False):
        """
        Retrieve soil moisture using the Oh(2002) model
        Output:
            mv: soil moisture (v/v)
            h: soil roughness (cm)
            rough_length: roughness length (cm)
        """
        hh = self.hh
        vv = self.vv
        hv = self.hv
        vh = self.vh
        theta = self.ia
        wl = self.wl

        p = hh-vv
        q = hv-vv        
        
        mv = np.empty(self.n)
        ks = np.empty(self.n)
        kl = np.empty(self.n)
        for i in xrange(self.n):
            if self.mask[i]:
                mv[i], ks[i], kl[i] = np.nan, np.nan, np.nan
            else:
                mv[i], ks[i], kl[i] = inverse_oh2002(p[i], q[i], vh[i], theta[i])

        k = 2*np.pi/wl
        h = ks/k        
        rough_length = kl/k 
        
        mv.shape = self.orig_shape
        h.shape = self.orig_shape
        rough_length.shape = self.orig_shape
        
        if output_rough_length:
            return mv, h, rough_length
        else:
            return mv, h
    
    def retrieve_oh2004(self):
        """
        Retrieve soil moisture using the Oh(2004) model
        Output:
            mv: soil moisture (v/v)
            h: soil roughness (cm)
        """
        hh = self.hh
        vv = self.vv
        hv = self.hv
        vh = self.vh
        theta = self.ia
        k = 2*np.pi/self.wl

        p = hh-vv
        q = hv-vv        
        
        mv = np.empty(self.n)
        h = np.empty(self.n)
        for i in xrange(self.n):
            if self.mask[i]:
                mv[i], h[i] = np.nan, np.nan
            else:
                mv[i], h[i] = inverse_oh2004(p[i], vh[i], theta[i], q[i], k[i])
        
        self.oh2004_range = {'min_kh':0.13, 'max_kh':6.98, 'min_theta':10, 
                             'max_theta':70, 'min_mv':0.04, 'max_mv':0.291}  
        mv.shape = self.orig_shape
        h.shape = self.orig_shape
        
        return mv, h
    
#def dubois_model(bc_file, ia_file, sm_file, h_file, l=5.6):
    #"""
    #It reads the backscatter coefficient and incidence angle image
    #and writes the soil moisture and soil roughness image
    #Input:
        #bc_file: path of the bc file *.tif (data in dB)
        #ia_file: path of the incidence angle file *.tif (data in radian)
        #sm_file: path of the output soil moisture file *.tif
        #h_file: path of the output soil roughness file *.tif
        #l: wavelength
    #Output:
        #None
    #"""
    ## read the BC data 
    #dataset = gdal.Open(bc_file,GA_ReadOnly)
    #geotransform = dataset.GetGeoTransform()
    #gcps = dataset.GetGCPs()
    #gcpproj = dataset.GetGCPProjection()
    #RasterXSize = dataset.RasterXSize
    #RasterYSize = dataset.RasterYSize    
    #
    #HH = dataset.GetRasterBand(1).ReadAsArray()
    #HV = dataset.GetRasterBand(2).ReadAsArray()
    #VH = dataset.GetRasterBand(3).ReadAsArray()
    #VV = dataset.GetRasterBand(4).ReadAsArray()
    #dataset = None
#
    ## mask the area for the hv-vv >11 dB
    #HH[(HV-VV)>-11] = np.nan   
    #
    ## read the IA data 
    #dataset = gdal.Open(ia_file,GA_ReadOnly)
    #IA = dataset.GetRasterBand(1).ReadAsArray()
    #dataset = None
    #IA = IA*180/np.pi # convert from radian to degree    
    #
    #sm = np.empty(HH.shape)
    #h = np.empty(HH.shape)
    #pb = PB(HH.shape[0])
    #for i in range(HH.shape[0]):
        #for j in range(HH.shape[1]):
            #if np.isnan(HH[i,j]*VV[i,j]*IA[i,j]):
                #sm[i,j], h[i,j] = np.nan, np.nan
            #else:
                #sm[i,j], h[i,j] = inverse_dubois(HH[i,j], VV[i,j], IA[i,j], l)
        #pb.grass()
#
    ## write the output soil moisture image    
    #driver = gdal.GetDriverByName('GTiff')
    #output_dataset = driver.Create(sm_file, RasterXSize, RasterYSize,1,gdal.GDT_Float32)
    #output_dataset.SetGeoTransform(geotransform)
    #output_dataset.SetGCPs(gcps, gcpproj)
    #output_dataset.GetRasterBand(1).WriteArray(sm, 0, 0)
    #output_dataset = None
    #
    ## write the output soil roughness image    
    #driver = gdal.GetDriverByName('GTiff')
    #output_dataset = driver.Create(h_file, RasterXSize, RasterYSize,1,gdal.GDT_Float32)
    #output_dataset.SetGeoTransform(geotransform)
    #output_dataset.SetGCPs(gcps, gcpproj)
    #output_dataset.GetRasterBand(1).WriteArray(h, 0, 0)
    #output_dataset = None
#
    #return None
#
if __name__ == "__main__":
    hh = [[-9, -5], [-9, -5], [-9, -5]]
    hv = [[-25, -32], [-25, -32], [-25, -32]]
    vh = [[-15, -20], [-15, -20], [-15, -20]]
    vv = [[-20, -27], [-20, -27], [-20, -27]]
    inci_angle = [[30, 20], [30, 20], [30, 20]]
    wl = 5.6
    foo_retrieve = inverse_radar(hh, hv, vh, vv, inci_angle, wl)
    print foo_retrieve.retrieve_dubois()
    print foo_retrieve.retrieve_oh1992()
    print foo_retrieve.retrieve_oh1994()
    print foo_retrieve.retrieve_oh2002()
    print foo_retrieve.retrieve_oh2004()
    
    #bc_file = '/home/tomer/radarsat_310513/bc_20m/20091222.tif'
    #ia_file = '/home/tomer/radarsat_310513/ia_20m/20091222.tif'
    #sm_file = '/home/tomer/temp/sm_20091222.tif'
    #h_file = '/home/tomer/temp/h_20091222.tif'
    #dubois_model(bc_file, ia_file, sm_file, h_file)
    #
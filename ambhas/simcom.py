'''
Created on Aug 13, 2014

@author: tomers
'''

from __future__ import division

import numpy as np
import matplotlib.pyplot as plt
import statistics as st
from scipy.interpolate import interp1d
from ambhas.nanlib import create_nan


def sigmoid(dt_csm, k, fpw=0, fpd=0):
    """
    Parameters:
    dt_csm: float
        temporal difference in the coarse scale soil moisture
    K: float
        a parameter
    fpw: float 
        fraction of the pixels permanently wet
    fpd: float
        fraction of the pixels permanently dry

    Output:
    fwet: float
        fraction of the pixels undergoing wetting
    fdry: float
        fraction of the pixels undergoing drying
    """
    fwet = fpw + (1-fpw-fpd)/(1+np.exp(-k*(dt_csm)))
    fdry = 1 - fwet

    return fwet, fdry

def th_dry_wet(rsm, fwet):
    """
    Parameters:
    rsm: 2d numpy array
        relative soil moisture
    fwet: float
        fraction of the pixels undergoing wetting

    Output:
    th: float
        threshold of the soil moisture for the pixels undergoing drying/wetting
    """
    f_x, x = st.cpdf(rsm[~np.isnan(rsm)].flatten(), h=0.05)
    foo = interp1d(f_x, x)
    if fwet<min(f_x):
        th = x.min()
    else:
        th = foo(fwet)
    
    return th

def area_drying_wetting(rsm, th):
    """
    Parameters:
    rsm: 2d numpy array
        relative soil moisture
    th: float
        threshold of the soil moisture for the pixels undergoing drying/wetting
    """
    area_drying = rsm > th
    area_wetting = rsm <= th
    return area_drying, area_wetting


def fun_ctg_ctl(rsm, a_ctg=1.0, a_ctl=1.0):
    """
    Parameters:
    rsm: 2d numpy array
        relative soil moisture
    a_ctg: float
        a parameter for ctg
    a_ctl: float
        a parameter for ctl
    """
    ctg = (1-rsm)**a_ctg
    ctl = rsm**a_ctl
    return ctg, ctl


def simcom(fsm_past, csm_current, csm_past, k, fc, wp, compute_fsss=True):
    """
    simple model for combining soil moisture at two different spatio-temporal scale

    Note: fsm_recent and csm_recent should be at the same time step

    Parameters:
    fsm_past: numpy 2d array
        fine scale soil moisture in recent past
    csm_current: float
        coarse scale soil moisture at current time step
    csm_past: float
        coarse scale soil moisture in recent past
    k: float
        a parameter

    Output:
    fscm_current: numpy 2d array
        fine scale soil moisture at current time step
    """
    #fsm_past *= csm_current/np.nanmean(fsm_past)

    dt_csm = csm_current - csm_past # temporal different in coarse scale soil moisture

    fwet, fdry = sigmoid(dt_csm, k)

    rsm = (fsm_past-wp)/(fc-wp)
    th = th_dry_wet(rsm, fwet)

    area_drying, area_wetting = area_drying_wetting(rsm, th)

    ctg, ctl = fun_ctg_ctl(rsm, 1.0, 1.0)

    try:
        min_ctl = np.min(ctl[area_drying])
    except:
        min_ctl = 0
    try:
        min_ctg = np.min(ctg[area_wetting])
    except:
        min_ctg = 0

    try:
        max_ctl = np.max(ctl[area_drying])
    except:
        max_ctl = 1.0
    try:
        max_ctg = np.max(ctg[area_wetting])
    except:
        max_ctg = 1.0
    #max_ctl = 0.48
    print min_ctl, max_ctl
    if compute_fsss:
        fsss = create_nan(ctg.shape)
        #fsss[area_drying] = -(ctl[area_drying] - min_ctl)
        #fsss[area_wetting] = ctg[area_wetting] - min_ctg
        #if dt_csm>0:
        #    fsss[area_drying] = -(ctl[area_drying] - min_ctl)/(max_ctl-min_ctl)
        #    fsss[area_wetting] = (ctg[area_wetting] - min_ctg)/(max_ctg-min_ctg)
        #else:
        #    fsss[area_drying] = 5*(ctl[area_drying] - min_ctl)/(max_ctl-min_ctl)
        #    fsss[area_wetting] = -(ctg[area_wetting] - min_ctg)/(max_ctg-min_ctg)
        
        fsss[area_drying] = 5.0*(ctl[area_drying] - min_ctl)/(max_ctl-min_ctl)
        fsss[area_wetting] = -(ctg[area_wetting] - min_ctg)/(max_ctg-min_ctg)
        print np.nanmean(fsss)

    else:
        fsss = np.ones(ctg.shape)

    fsss = fsss/np.nanmean(fsss)

    fsm_current = fsm_past + fsss*dt_csm

    return fsm_current, fsss, ctl, area_drying


if __name__ == '__main__':
#===============================================================================
#     # test with real data
#     import gdal
#     from osgeo.gdalconst import *
#     from ambhas.errlib import rmse, bias, correlation
#     eco_file = '/home/tomers/ecoclimap/processed/XB_100m.tif'
#     dataset = gdal.Open(eco_file, GA_ReadOnly)
#     eco = dataset.GetRasterBand(1).ReadAsArray()
#     dataset = None
#     forest = np.zeros((eco.shape))
#     forest[eco<=38] = 1
# 
#     wp_file = '/home/tomers/radarsat_310513/soil/wp_100m.tif'
#     fc_file = '/home/tomers/radarsat_310513/soil/fc_100m.tif'
#     fid = gdal.Open(fc_file, GA_ReadOnly)
#     fc = fid.GetRasterBand(1).ReadAsArray()
#     fid = None
#     fid = gdal.Open(wp_file, GA_ReadOnly)
#     wp = fid.GetRasterBand(1).ReadAsArray()
#     fid = None
# 
#     # read the RADARSAT data 
#     ssm_past_file = '/home/tomers/radarsat_310513/opr/ssm_100m/20120707.tif'
#     fid = gdal.Open(ssm_past_file, GA_ReadOnly)
#     fsm_past = fid.GetRasterBand(1).ReadAsArray()
#     fid = None
# 
#     ssm_current_file = '/home/tomers/radarsat_310513/opr/ssm_100m/20120731.tif'
#     fid = gdal.Open(ssm_current_file, GA_ReadOnly)
#     fsm_current_obs = fid.GetRasterBand(1).ReadAsArray()
#     fid = None
#     
#     #csm_current = 0.100284626905
#     #csm_past = 0.142431498605
#     csm_current = np.nanmean(fsm_current_obs)
#     csm_past = np.nanmean(fsm_past)
#     
#     fsm_past[forest==1] = np.nan # apply forest cover
#     fsm_current_obs[forest==1] = np.nan # apply forest cover
#     
#     print csm_past - csm_current
#     k = 41.0
#     
#     fsm_current_mod2, fsss2, ctl, area_drying = simcom(fsm_past, csm_current, csm_past, k, fc, wp)
#     fsm_current_mod1, fsss, ctl, area_drying = simcom(fsm_past, csm_current, csm_past, k, fc, wp, compute_fsss=False)
# 
#     rmse_sm1 = rmse(fsm_current_mod1, fsm_current_obs)
#     bias_sm1 = bias(fsm_current_mod1, fsm_current_obs)
#     corr_sm1 = correlation(fsm_current_mod1, fsm_current_obs)
# 
#     rmse_sm2 = rmse(fsm_current_mod2, fsm_current_obs)
#     bias_sm2 = bias(fsm_current_mod2, fsm_current_obs)
#     corr_sm2 = correlation(fsm_current_mod2, fsm_current_obs)
# 
#     #print np.nansum(fsm_current_mod2<fsm_past)
#     #print np.nansum(fsm_current_mod1<fsm_past)
# 
#     plt.plot(fsm_current_obs, fsm_current_mod2, '.g')
#     plt.plot(fsm_current_obs, fsm_current_mod1, '.m')
#     plt.plot([0,0.3],[0,0.3], 'k', lw=2)
#     plt.xlabel('RADARSAT SSM (v/v)')
#     plt.ylabel('SMOS Disaggregated SSM (v/v)')
#     plt.tight_layout()
#     #plt.xlim(0.0,1.0)
#     #plt.ylim(0.0,1.0)
#     plt.text(0.12, 0.25, ' RMSE = %.3f \n Bias = %.2f \n R = %.2f'%(rmse_sm2, bias_sm2, corr_sm2))
#     plt.text(0.12, 0.05, ' RMSE = %.3f \n Bias = %.2f \n R = %.2f'%(rmse_sm1, bias_sm1, corr_sm1))
#     #plt.title('Disaggregated for %2d/%02d/%4d by using %2d/%02d/%4d'%(
#     #day[i+1],month[i+1],year[i+1], day[i],month[i],year[i]))
#     fig_png = '../temp/comsom_scatt.png'
#     plt.savefig(fig_png)
#     plt.close()
# 
#     #plt.matshow(fsm_current_obs,vmin=0.1,vmax=0.3)
#     plt.matshow(fsm_current_obs)
#     plt.colorbar(shrink=0.7)
#     plt.axis('off')
#     plt.title('RADARSAT-2 retrieved')
#     #plt.tight_layout()
#     fig_png = '../temp/obs_fsm_pattern.png'
#     plt.savefig(fig_png)
#     plt.close()
# 
#     plt.matshow(fsm_current_mod1)
#     #plt.matshow(fsss2)
#     plt.colorbar(shrink=0.7)
#     plt.axis('off')
#     plt.title('Disaggregated')
#     #plt.tight_layout()
#     fig_png = '../temp/mod_fsm_pattern.png'
#     plt.savefig(fig_png)
#     plt.close()
#===============================================================================

   
#===============================================================================
     fsm_past = 0.8*np.random.uniform(size=(5, 5))
     fsm_past[2,2] = np.nan
     csm_past = np.nanmean(fsm_past)
 
     csm_current = 0.5*csm_past
     k = 1.0
     fc = 1.0
     wp = 0.0
     fsm_current1, fsss, ctl, area_drying = simcom(fsm_past, csm_current, csm_past, k, fc, wp, compute_fsss=False)
     fsm_current2, fsss, ctl, area_drying = simcom(fsm_past, csm_current, csm_past, k, fc, wp)
     print np.nanmean(fsm_current2)-np.nanmean(fsm_past) #, np.sum(fsm_past<fsm_current2)/np.size(fsm_current2)
 
     plt.subplot(2, 2, 1)
     plt.imshow(fsm_past, interpolation='nearest')
     plt.axis('off')
     plt.colorbar()
 
     plt.subplot(2, 2, 2)
     plt.imshow(fsss, interpolation='nearest')
     plt.axis('off')
     plt.colorbar()
 
     plt.subplot(2, 2, 3)
     plt.imshow(fsm_current2, interpolation='nearest')
     plt.axis('off')
     plt.colorbar()
 
     plt.subplot(2, 2, 4)
     plt.plot(fsm_past, fsm_current2, '.k')
     plt.plot([0, 1], [0, 1], 'r', lw=2)
 
     plt.savefig('../temp/temp.png')

     print('processing over')
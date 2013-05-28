# -*- coding: utf-8 -*-
"""
Created on Tue May 28 17:16:11 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

from sunlib import sun
import numpy as np

def sat_vap_pressure(Tav):
    """
    Computes saturation vapor pressure using the Eq. given by
    Tetens (1930) and Murray (1967)
    
    Input:
        Tav: mean daily air temperature (deg C)
    Output:
        e0: saturation vapor pressure (kPa)
    """
    e0 = np.exp((16.78*Tav-116.9)/(Tav+237.3))
    return e0

def latent_head_vap(Tav):
    """
    Computes latent heat of vaporization using the Eq. given by
    Harrison (1963)
    
    Input:
        Tav: mean daily air temperature (deg C)
    Output:
        l: latent heat of vaporization (MJ kg^{-1})
    """
    l = 2.501 - 2.361E-3*Tav
    return l

def atmospheric_pressure(EL):
    """
    Computes atmospheric pressure using an equation developed by 
    Doorenbos and Pruitt (1977)
    
    Input:
        EL: elevation (m)
        
    Output:
        P: atmospheric pressure (kPa) 
    
    """
    P = 101.3-0.01152*EL+0.544E-6*EL**2
    return P

def psychrometric_constant(Tav, EL=0,cp=1.013E-3):
    """
    Input:
        Tav: mean daily air temperature (deg C)
        EL: elevation (m)
        cp: specific heat of moist air at constant pressure (MJ kg^{-1} C^{-1})
    Output:
        gamma: psychrometric constant (kPa C^{-1}) 
    """
    l =  latent_head_vap(Tav)
    P = atmospheric_pressure(EL)
    gamma = cp*P/(0.622*l)
    return gamma

def pm(Hnet, Tav, Rh, uz, EL=0, co2 = 330):
    """
    Compute the potential evapotranspiration using the Penman-Monteith equation
    for a reference (alfalfa) crop

    Ref: Neitsch, S.L., J.G. Arnold, J.R. Kiniry, J.R. Williams,
    and King, K.W., (2002) Soil and Water Assessment
    Tool - Theoretical Documentation, version 2000.
    Temple, TX : Blackland Research Center, Texas
    Agricultural Experiment Station.
    
    Input:
        Hnet: Daily net radiation (MJm^{-2}d&{-1})
        Tav: mean air temperature for the day (deg C)
        Rh: relative humidity
        uz: wind speed (m/s)
        EL: elevation (m)
        co2: co2 concentration (ppmv)
    
    """
    
    # net radiation     (chapter 1:1)
    #Hnet = 
    
    # latent heat of vaporization (chapter 1:2)
    l =  latent_head_vap(Tav)
    
    # the psychrometric constant (chapter 1:2)
    gamma = psychrometric_constant(Tav, EL)
    
    #saturation vapor pressure (chapter 1:2)
    e0 = sat_vap_pressure(Tav)
    
    # actual vapor pressure (chapter 1:2)
    e = Rh*e0

    # slope of the saturation vapor pressure-temperature curve (chapter 1:2)
    delta = 4098*e0/(Tav+237.3)**2
    
    # soil heat flux
    G = 0
    
    # combined term
    combined_term = 1710-6.85*Tav
    
    # canopy resistance
    rc = 49/(1.4-0.4*co2/330)
        
    # aerodynamic resistance
    ra = 114/uz

    LE = (delta*(Hnet-G)+ gamma*combined_term*(e0-e)/ra)/(delta+gamma*(1+rc/ra))
    PET = LE/l
    
    return PET
    

def pt(Hnet, Tav, EL=0):
    """
    Compute the potential evapotranspiration using the Priestley and Taylor equation
    for a reference (alfalfa) crop

    Ref: Neitsch, S.L., J.G. Arnold, J.R. Kiniry, J.R. Williams,
    and King, K.W., (2002) Soil and Water Assessment
    Tool - Theoretical Documentation, version 2000.
    Temple, TX : Blackland Research Center, Texas
    Agricultural Experiment Station.
    
    Input:
        Hnet: Daily net radiation (MJm^{-2}d&{-1})
        Tav: mean air temperature for the day (deg C)
        EL: elevation (m)
    Output:
        PET: 
    """
    # constants
    G = 0
    alpha_pet = 1.28
    
    e0 = sat_vap_pressure(Tav)
    delta = 4098*e0/(Tav+237.3)**2
    l =  latent_head_vap(Tav)
    gamma = psychrometric_constant(Tav, EL)
    
    LE = alpha_pet*(delta/(delta+gamma))*(Hnet-G)
    PET = LE/l
    
    return PET
    

def hm(Tmx, Tmn, lat_deg, lon_deg, doy,ze=5.5):
    """
    Compute the potential evapotranspiration using the Hargreaves method
    for a reference (alfalfa) crop

    Ref: Neitsch, S.L., J.G. Arnold, J.R. Kiniry, J.R. Williams,
    and King, K.W., (2002) Soil and Water Assessment
    Tool - Theoretical Documentation, version 2000.
    Temple, TX : Blackland Research Center, Texas
    Agricultural Experiment Station.
    
    Input:
        Tmx: maximum air temperature for the day (deg C)
        Tmn: minimum air temperature for the day (deg C)
        lat_deg:        latitude in degree ( south is negative)
        lon_deg:        longitude in degree (west is negative)
        doy:            day of year
        ze :            time zone in hour
        
        
        Hnet: Daily net radiation (MJm^{-2}d&{-1})
        Tav: mean air temperature for the day (deg C)
        EL: elevation (m)
    Output:
        PET: 
    """
    foo = sun(doy, lat_deg, lon_deg)
    H0 = foo.daily_ETR()
    LE = 0.0023*H0*np.sqrt((Tmx-Tmn))*(Tav+17.8)
    l = latent_head_vap(Tav)
    PET = LE/l
    
    return PET

def rs(Rs, Tav):
    """
    Input:
        Rs: Shortwave radiation (MJ m^{-2} day^{-1})
        Tav: mean air temperature for the day (deg C)
    Output:
        PET
    """
    
    PET = -0.611+0.149*Rs+0.079*Tav
    
    return PET

def rn(Rn, Tav):
    """
    Input:
        Rn: net radiation (MJ m^{-2} day^{-1})
        Tav: mean air temperature for the day (deg C)
    Output:
        PET
    """
    
    PET = 0.489 + 0.289*Rn + 0.023*Tav
    
    return PET

if __name__ == '__main__':
    # pm
    Hnet = 100
    Tav = 15
    Rh = 0.8
    uz = 5
    EL = 800
    print pm(Hnet, Tav, Rh, uz, EL, co2 = 330)
    
    # pt
    print pt(Hnet, Tav, EL)
    
    #hm
    lat_deg = 11
    lon_deg = 76
    doy = 180
    Tmx = 20
    Tmn = 10
    print hm(Tmx, Tmn, lat_deg, lon_deg, doy,ze=5.5)
 
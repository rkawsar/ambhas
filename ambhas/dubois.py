# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 11:25:46 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

import numpy as np
from scipy.optimize import fmin
import matplotlib.pyplot as plt
from ambhas.dielectric import ep2mv

def dubois_forward(h, ep, theta, wl, dB=True):
    """
    This function performs the forward modelling using the Dubois model
    Input:
        h: rms height (cm)
        ep: real part of the dielectric constant
        theta: incidence angel (degree)
        wl: wavelength (cm)
        dB: the type of output
            True --> hh, vv in dB
            False --> hh, vv in linear      
    Output:
        hh: backscatter coefficient in hh pol (in dB if dB=True)
        vv: backscatter coefficient in vv pol (in dB if dB=True)
    """
    #convert theta from degree to radian
    theta_rad = theta*np.pi/180.0
    # k is wave number (2*pi/l)
    k = 2*np.pi/wl
    # convert mv into ep
    hh = 10**(-2.75)*((np.cos(theta_rad)**1.5)/(np.sin(theta_rad**5)))*10**(
    0.028*ep*np.tan(theta_rad))*(k*h*np.sin(theta_rad)**1.4)*wl**0.7
    vv = 10**(-2.35)*((np.cos(theta_rad)**3.0)/(np.sin(theta_rad)))*10**(
    0.046*ep*np.tan(theta_rad))*(k*h*np.sin(theta_rad)**3.0)**1.1*wl**0.7
    
    if dB:
        hh = 10*np.log10(hh)
        vv = 10*np.log10(vv)
    
    return hh,vv

def err_dubois(ep_h, hh=-15, vv=-20, theta=20, wl=5.6):
    """
    Eq. 6 of Oh (2004)
    Input:
        ep_h: a vector containing ep and h
        ep_h[0]: ep
        ep_h[1]: h
        hh: backscatter coefficient in hh (dB)
        vv: backscatter coefficient in vv (dB)
        theta: incidence angle (degree)
        l: wavelength (cm)
    """
    ep =  ep_h[0]
    h =  ep_h[1]
    
    # compute the error
    estimated_hh, estimated_vv = dubois_forward(h, ep, theta, wl)
    err = np.sqrt((estimated_hh - hh)**2 + (estimated_vv - vv)**2)
    return err

def estimate_ep_h(hh, vv, theta, wl):
    """
    This function performs the forward modelling using the Dubois model
    Input:
        hh: backscatter coefficient in hh pol (in dB if dB=True)
        vv: backscatter coefficient in vv pol (in dB if dB=True)
        theta: incidence angel (degree)
        wl: wavelength (cm)
    Output:
        h: rms height (cm)
        ep: real part of the dielectric constant
    """
    ep_h = fmin(err_dubois, [10,1], args=(hh, vv, theta, wl), ftol=0.01, disp=False)
    
    return ep_h 
    
def inverse_dubois(hh, vv, theta, wl):
    """
    This function performs the forward modelling using the Dubois model
    Input:
        hh: backscatter coefficient in hh pol (dB)
        vv: backscatter coefficient in vv pol (dB)
        theta: incidence angel (degree)
        wl: wavelength (cm)
    Output:
        mv: soil moisture
        h: rms height (cm)        
    """
    ep_h = estimate_ep_h(hh, vv, theta, wl)
    ep = ep_h[0]
    h = ep_h[1]
    mv = ep2mv(ep)
    
    return mv, h
    

if __name__ == "__main__":
    # perform sensitiviy analysis    
    # fig. 4 of Dubois (1995)
    ep = 10
    h = 1
    theta = 20
    wl = 5.6
    hh,vv =  dubois_forward(h, ep, theta, wl)
    print(hh,vv)

    #     
    print inverse_dubois(hh, vv, theta, wl)
    
    # perturb with errors
    # Fig. 4(a)
    Ca = np.linspace(-3,3,51)
    hh = hh - Ca
    vv = vv - Ca
    
    estimated_ep = np.empty(51,)
    for i in range(51):
        estimated_ep[i] = estimate_ep_h(hh[i], vv[i], theta, l)[0]
    
    # dielectric function
    ep_fn = lambda ep: (-530+292*ep-5.5*ep**2+0.043*ep**3)*1e-4        
    
    plt.plot(Ca, ep_fn(estimated_ep)-ep_fn(ep))
    plt.show()
    
    
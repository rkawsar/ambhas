# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 17:37:07 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

from __future__ import division

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fmin
from ambhas.dielectric import mv2ep, ep2mv

def foreward_model(ks, gamma0, theta):
    """
    Eq. 4 of Oh (1992)
    Input:
        ks
        gamma0: Fresnel reflectivity
        theta: incidence angle (degree)    
    Output:
        p: hh-vv (dB)  
        q: hv-vv (dB)             
    """
    # convert theta from degree to radian
    theta = theta*np.pi/180
    
    q = 0.25*np.sqrt(gamma0)*(0.1+np.sin(theta)**0.9)*(1-np.exp(-(1.4-1.6*gamma0)*ks))
    p = (1 - (2*theta/np.pi)**(0.314/gamma0)*np.exp(-ks))**2
    
    return 10*np.log10(p), 10*np.log10(q)
    
def ep2gamma(ep):
    """
    Eq. 5 of Oh(1992)
    """
    gamma0 = (np.abs((1-np.sqrt(ep))/(1+np.sqrt(ep))))**2
    return gamma0
    
def gamma2ep(gamma):
    """
    Inverse of the eq. 5 of Oh(1992)
    """
    ep = (2/(1-np.sqrt(gamma))-1)**2
    return ep


def res_ks_gamma0(ks_gamma0, p, q, theta):
    """
    compute error in the Eq. 11 of Oh (1992)
    Input:
        
        gamma0: Fresnel reflectivity
        p: hh-vv (dB)
        q: hh-vv (dB)
        theta: incidence angle (degree)
        
    """
    ks = ks_gamma0[0]
    gamma0 = ks_gamma0[1]
    
    # compute the error
    sim_p, sim_q = foreward_model(ks, gamma0, theta)
    res = np.sqrt((sim_p-p)**2 + (sim_q-q)**2)
    
    return res
    
def estimate_ks_gamma0(p, q, theta):
    """
    Input:
        p: (dB)
        q: (dB)
        theta: incidence angle (degree)
            
    """
    
    guess_ks_gamma0 = [0.2, 0.4]
    ks_gamma0 = fmin(res_ks_gamma0, guess_ks_gamma0, args=(p, q, theta), disp=False)
    ks = ks_gamma0[0]
    gamma0 = ks_gamma0[1]
    return ks, gamma0

def inverse_oh1994(p, q, theta):
    """
    
    """
    ks, gamma0 = estimate_ks_gamma0(p, q, theta)
    ep = gamma2ep(gamma0)
    
    mv = ep2mv(ep)
    
    return mv, ks


if __name__ == "__main__":
    mv = 0.15
    ks = 0.3
    theta = 40
    ep = mv2ep(mv)
    gamma0 = ep2gamma(ep)
    p,q =  foreward_model(ks, gamma0, theta)
    print inverse_oh1994(p, q, theta)
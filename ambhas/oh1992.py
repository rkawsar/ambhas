# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 16:22:20 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""
from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fmin
from ambhas.dielectric import ep2mv

def foreward_model(ks, gamma0, theta):
    """
    Eq. 4 of Oh (1992)
    Input:
        ks
        gamma0: Fresnel reflectivity
        theta: incidence angle (degree)    
    Output:
        q: hh-vv (dB)
                
    """
    
    theta = theta*np.pi/180 # convert theta from degree to radian
    
    q = 0.23*np.sqrt(gamma0)*(1-np.exp(-ks))
    p = (1 - (2*theta/np.pi)**(1/(3*gamma0))*np.exp(-ks))**2
    
    return 10*np.log10(q), 10*np.log10(p)

def res_eq11(gamma0, p, q, theta):
    """
    compute error in the Eq. 11 of Oh (1992)
    Input:
        gamma0: Fresnel reflectivity
        p: hh-vv (dB)
        q: hh-vv (dB)
        theta: incidence angle (degree)
        
    """
    # convert from dB to linear
    p = 10**(p/10.0)
    q = 10**(q/10.0)
    # convert theta from degree to radian
    theta = theta*np.pi/180
    # compute the error
    res = (2*theta/np.pi)**(1/(3*gamma0))*(1-q/(0.23*np.sqrt(gamma0))) + np.sqrt(p) - 1
    
    return res**2


def estimate_gamma(p, q, theta):
    """
    Eq. 11 of Oh(1992)
    Input:
        p: hh-vv (dB)
        q: hh-vv (dB)
    """
    gamma0 = fmin(res_eq11, 0.36, args=(p,q,theta), ftol=0.0001, disp=False)[0]
    
    return gamma0
    
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

def inverse_oh1992(p,q,theta):
    """
    Eq. 11 of Oh(1992)
    Input:
        p: hh-vv (dB)
        q: hv-vv (dB)
        theta: incidence angle (degree)
    Output:
        mv: surface soil moisture (v/v)
        ks: microwave roughness
    """
    # estimate mv
    gamma0 = estimate_gamma(p, q, theta)
    ep = gamma2ep(gamma0)
    mv = ep2mv(ep)
    
    # estimate ks
    # convert from dB to linear
    q = 10**(q/10.0)
    ks = -np.log(1 - q/(0.23*np.sqrt(gamma0)))
    
    return mv, ks
    
if __name__ == "__main__":
    from ambhas.dielectric import mv2ep
    # fig 11 and 12 of Oh(1992)
    theta = 40
    mv = 0.25
    ep = mv2ep(mv)
    gamma0 = ep2gamma(ep)
    ks = np.linspace(0,7)
    q, p =  foreward_model(ks, gamma0, theta)
    
    #plt.plot(ks,q)
    #plt.show()
    
    #plt.plot(ks,p)
    #plt.show()

    
    # inverse modelling    
    ks = 0.1
    theta = 40
    mv = 0.35
    ep = mv2ep(mv)
    gamma0 = ep2gamma(ep)
    print gamma0
    q, p =  foreward_model(ks, gamma0, theta)
    print inverse_oh1992(p, q, theta)
    
    print p,q
    
    
    
    
    
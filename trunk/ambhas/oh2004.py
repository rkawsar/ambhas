# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 14:59:54 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

from __future__ import division

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fmin

def vh_fun(theta, mv, k, s):
    """
    Eq. 1 of Oh(2004)
    Input:
        theta: incidence angle (degree)
        mv: soil moisture (v/v)
        k: wave number (k = 2*pi/l), where l is wavelenght in cm
        s: rms height (cm)
    
    Output:
        p: hh-vv (dB)
    """
    ks = k*s
    # convert the theta from deg to radian
    theta = theta*np.pi/180
    vh = 0.11*mv**0.7*(np.cos(theta))**2.2*(1-np.exp(-0.32*ks**1.8))
    return 10*np.log10(vh)
    
    
def ks2p(theta, mv, k, s):
    """
    Eq. 2 of Oh(2004)
    Input:
        theta: incidence angle (degree)
        mv: soil moisture (v/v)
        k: wave number (k = 2*pi/wl), where wl is wavelenght in cm
        s: rms height (cm)
    
    Output:
        p: hh-vv (dB)
    """
    ks = k*s
    p = 1 - (theta/90)**(0.35*mv**(-0.65)) * np.exp(-0.4*(ks**1.4))
    return 10*np.log10(p)
    

def pmax(theta,k):
    """
    Maximum feasible value of the p (dB)
    """
    s = 5.5
    mv = 0.01
    return ks2p(theta, mv, k, s)


def ks_fun(theta, mv, vh):
    """
    Eq. 5 of Oh(2004)
    Input: 
        theta: incidence angle (degree)
        mv: soil moisture (v/v)
        vh: backscatter coefficient in vh (dB)
    """
    # convert the theta from deg to radian
    theta = theta*np.pi/180
    # convert vh from dB to linear scale
    vh = 10**(vh/10.0)
    ks = (-3.125*np.log(1-vh/(0.11*mv**0.7*(np.cos(theta))**2.2)))**0.556
    return ks


def eq6(mv, p=-1, vh=-20, theta=20):
    """
    Eq. 6 of Oh (2004)
    Input:
        mv: soil moisture (v/v)
        p: measured p value (dB)
        vh: backscatter coefficient in vh (dB)
        theta: incidence angle (degree)
    """
    # convert p from dB to linear scale
    p = 10**(p/10.0)
    ks = ks_fun(theta, mv, vh)
    err = 1 - (theta/90)**(0.35*mv**(-0.65)) * np.exp(-0.4*(ks**1.4)) - p
    return err**2
    

def mv1_ks1(p, vh, theta):
    """
    Minimize the Eq. 6 of Oh (2004)
    Input:
        p: vh-vv (dB)
        vh: backscatter coefficient in vh (dB)
        theta: incidence angle (degree)
    """
    mv = fmin(eq6, 0.1, args=(p,vh,theta), ftol=0.01, disp=False)[0]
    ks = ks_fun(theta, mv, vh)
    return mv, ks

def eq4(theta,k,s):
    """
    Eq. 4 of Oh (2004)
    Input:
        theta: incidence angle (degree)
        k: wave number (k = 2*pi/l), where l is wavelenght in cm
        s: rms height (cm)
    
    Output:
        q: hh-vv (dB)
    """
    ks = k*s
    # convert the theta from deg to radian
    theta = theta*np.pi/180
    q = 0.095*(0.13+np.sin(theta))**1.4*(1-np.exp(-1.3*ks**0.9))
    
    return 10*np.log10(q)

def inverse_eq4(theta, q):
    """
    Inverse of the Eq. 4 of Oh (2004)
    Input:
        theta: incidence angle (degree)
        q: hh-vv (dB)
    Output:
        ks: k*s
    """
    # convert q from dB to linear scale
    q = 10**(q/10.0)
    # convert the theta from deg to radian
    theta = theta*np.pi/180
    ks = (-(np.log(1-q/(0.095*(0.13+np.sin(theta))**1.4)))/1.3)**(1/0.9)
    
    return ks
    
def mv2_mv3_ks2(theta, q, p, vh):
    """
    Estimate the mv2,mv3,ks2
    
    Input:
        theta: incidence angle (degree)
        q: hh-vv (dB)
        p: vh-vv (dB)
        vh: (dB)
    Output:
        mv2: soil moisture (v/v)
        mv3: soil moisture (v/v)
        ks2: 
    """
    ks2 = inverse_eq4(theta, q)
    # convert p from dB to linear scale
    p = 10**(p/10.0)
    
    foo = (1-p)/(np.exp(-0.4*ks2**1.4))    
    mv2 = (np.log(foo)/(0.35*np.log(theta/90)))**(-1/0.65)
    
    # convert vh from dB to linear scale
    vh = 10**(vh/10.0)
    # convert the theta from deg to radian
    theta = theta*np.pi/180
    mv3 = (vh/(0.11*(np.cos(theta))**2.2*(1-np.exp(-0.32*ks2**1.8))))**(1/0.7)
    
    return mv2,mv3,ks2
    
def inverse_oh2004(p, vh, theta, q, k):
    """
    Input:
        p: vh-vv (dB)
        vh: (dB)
        theta: incidence angle (degree)
        q: hh-vv (dB)
        k: (k = 2*pi/l), where l is wavelenght in cm
    Output:
        mv:
        s:
    """
    # compute pmax
    if p>pmax(theta,k):
        s = np.nan #5.5
        mv = np.nan #0.01
    else:
        # compute mv1, s1
        mv1, s1 = mv1_ks1(p, vh, theta)
        
        # compute s2, mv2, mv3
        mv2, mv3, ks2 = mv2_mv3_ks2(theta, q, p, vh)
        s2 = ks2/k
    
        # weighting
        w = [1,1/4,1,1,1]
        s = (w[0]*s1 + w[1]*s2)/(w[0] + w[1])
    
        mv = (w[2]*mv1 + w[3]*mv2 + w[4]*mv3)/(w[2] + w[3] + w[4])
    
    return mv, s


if __name__ == "__main__":
    pass
    # Fig. 1(s) of Oh (2004)
    #theta = 45
    #mv = np.arange(0.04,0.29,0.05)
    #k = 2*np.pi/5.6
    #s = np.arange(0.13,6.98,0.5)/k
    #MV, S = np.meshgrid(mv,s)
    #vh = vh_fun(theta, MV, k, S)
    #
    #plt.pcolor(mv,s, vh)
    #plt.colorbar()
    #plt.show()
    #
    ## Fig. 1(b) of Oh (2004)
    #p = ks2p(theta, MV, k, S)
    #plt.pcolor(mv,s, p)
    #plt.colorbar()
    #plt.show()
    #
    ## print pmax
    #print pmax(theta,k)
    #
    #vh = -25.0
    #mv = 0.25
    #print ks_fun(theta, mv, vh)
    
    ################### check the inverse modelling
    # perform foreward modelling
    theta = 25
    mv = 0.25
    k = 2*np.pi/5.6
    s = 1.1/k
    p = ks2p(theta, mv, k, s)
    vh = vh_fun(theta, mv, k, s)
    q = eq4(theta,k,s)
    print('mv=%.2f vh=%.2f '%(mv, vh))
    
    # perform inverse modelling
    #print mv1_ks1(p, vh, theta)
    #print mv2_mv3_ks2(theta, q, p, vh)
    print inverse_oh2004(p, vh, theta, q, k)
    # fig 2    
    theta = 40
    k = 2
    s = 1
    
    #print q
    #print inverse_eq4(theta,q)
    
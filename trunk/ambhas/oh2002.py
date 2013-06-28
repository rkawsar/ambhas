# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 10:21:26 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

from __future__ import division

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fmin

def vh_fun(mv, theta, ks):
    """
    Eq. (12) of Oh (2002)
    Input:
        mv: soil moisture (v/v)
        theta: incidence angle (degree)
        ks: electromagnetic roughness
    Output:
        vh: vh(dB)
    """
    a,b,c,d,e = 0.11, 0.7, 2.2, 0.32, 1.8
    # convert theta from degree to radian
    theta = theta*np.pi/180
    vh = a*mv**b*(np.cos(theta))**c*(1-np.exp(-d*ks**e))
    return 10*np.log10(vh)

def p_fun(mv, theta, ks):
    """
    Eq. (12) of Oh (2002)
    Input:
        mv: soil moisture (v/v)
        theta: incidence angle (degree)
        ks: electromagnetic roughness
    Output:
        vh: vh(dB)
    """
    a,b,c,d = 0.35, 0.65, 0.4, 1.4
    p = 1 - (theta/90)**(a*mv**-b)*np.exp(-c*ks**d)
    return 10*np.log10(p)

def q_fun(theta, ks, kl):
    """
    Eq. (13) of Oh (2002)
    Input:
        theta: incidence angle (degree)
        ks: electromagnetic roughness
        kl: wave number * correlation length
    Output:
        q: (dB)
    """
    a,b,c,d,e = 0.10, 1.3, 1.2, 0.9, 0.8
    theta = theta*np.pi/180 # convert theta from degree to radian
    q = a*(ks/kl + np.sin(b*theta))**c * (1-np.exp(-d*ks**e))
    return 10*np.log10(q)

def res_mv_ks(mv_ks, p, vh, theta):
    """
    this function computes the error between the 
    simulated and measured p and vh
    Input:
        mv_ks[0]: mv
        mv_ks[1]: ks
        p: (dB)
        vh: (dB)
        theta: incidence angle (degree)
            
    """
    mv = mv_ks[0]
    ks = mv_ks[1]
    sim_p = p_fun(mv, theta, ks)
    sim_vh = vh_fun(mv, theta, ks)
    res = (sim_p-p)**2 + (sim_vh-vh)**2
    return res

def estimate_mv_ks(p, vh, theta):
    """
    Input:
        p: (dB)
        vh: (dB)
        theta: incidence angle (degree)
            
    """
    guess_mv_ks = [0.1, 1]
    mv_ks = fmin(res_mv_ks, guess_mv_ks, args=(p, vh, theta), disp=False)
    mv = mv_ks[0]
    ks = mv_ks[1]
    return mv, ks

def estimate_kl(ks, theta, q):
    """
    Input:
        ks: microwave roughness
        theta: incidence angle (degree)
        q: (dB)
    Output:
        kl
    """
    a,b,c,d,e = 0.10, 1.3, 1.2, 0.9, 0.8
    
    q = 10**(q/10) # convert from dB to linear 
    theta = theta*np.pi/180 # convert from degree to radian
    kl = ks/(((q/a)/(1-np.exp(-d*ks**e)))**(1/c) - np.sin(b*theta))

    return kl

def inverse_oh2002(p, q, vh, theta):
    """
    Input:
        p: (dB)
        q: (dB)
        vh: (dB)
        theta: incidence angle (degree)
    Output:
        mv:
        ks:
        kl:
    """
    mv, ks = estimate_mv_ks(p, vh, theta)
    kl = estimate_kl(ks, theta, q)
    
    return mv, ks, kl

if __name__ == "__main__":
    # Fig. 3 of Oh(2002)
    ks = np.logspace(-1, 1)
    mv = 0.13
    theta = 45
    vh = vh_fun(mv, theta, ks)
    #plt.semilogx(ks, vh)
    #plt.show()
    
    # Fig. 4 of Oh(2002)
    ks = np.logspace(-1, 1)
    kl = 4*ks
    mv = 0.20
    theta = 40
    q = q_fun(theta, ks, kl)
    #plt.semilogx(ks, q)
    #plt.show()
    
    # Fig. 6 of Oh(2002)
    ks = np.logspace(-1, 1)
    mv1, theta1 = 0.03, 10
    mv2, theta2 = 0.3, 70
    p1 = p_fun(mv1, theta1, ks)
    p2 = p_fun(mv2, theta2, ks)
    
    #plt.semilogx(ks, p1)
    #plt.semilogx(ks, p2)
    #plt.show()

    
    
    # foreward modelling
    mv = 0.3
    theta = 20
    ks = 0.1
    kl = 0.5*ks
    p = p_fun(mv, theta, ks)
    vh = vh_fun(mv, theta, ks)
    q = q_fun(theta, ks, kl)
    #print estimate_mv_ks(p, vh, theta)
    #print estimate_kl(ks, theta, q)
    print inverse_oh2002(p, q, vh, theta)
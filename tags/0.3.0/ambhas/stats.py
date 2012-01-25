# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 15:24:08 2011

@author: Sat Kumar Tomer
@website: www.ambhas.com
@email: satkumartomer@gmail.com
"""

from __future__ import division
import numpy as np
import statistics as st
from scipy.interpolate import interp1d

def bias_correction(oc, mc, mp):
    """
    Input:
        oc: observed current
        mc: modeled current
        mp: modeled prediction     
    
    Output:
        mp_adjusted: adjusted modeled prediction
        
        
    """
    
    # convert the input arrays into one dimension
    oc = oc.flatten()
    mc = mc.flatten()
    mp = mp.flatten()    
    
    # Instead of directly inverting the CDF, linear interpolation using 
    # interp1d is used to invert the CDF.
    
    F_oc, OC = st.cpdf(oc, n=1000)
    f = interp1d(F_oc, OC)
    
    F1 = st.cpdf(mc, mp)
    mp_adjusted = f(F1)
    
    return mp_adjusted
    
    
if __name__ == "__main__":
    oc = np.random.randn(100)
    mc = 2+np.random.randn(100)
    mp = 2+np.random.randn(1000)
    
    print("mean of observed current is %f"%oc.mean())
    print("mean of modeled current is %f"%mc.mean())
    print("mean of modeled prediction is %f"%mp.mean())
    
    mp_adjusted = bias_correction(oc, mc, mp)
    print("mean of adjusted modeled prediction is %f"%mp_adjusted.mean())

    
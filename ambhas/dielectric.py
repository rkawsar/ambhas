# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 12:28:04 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

import numpy as np
import warnings
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

def ep2mv(ep):
    """
    this function converts the real part of dielectric constant
    into the volumetric soil moisture
    
    The regression equation is based on the Topp et al. (1980,1985)
    Input:
        ep: real part of the dielectric constant
    Output:
        mv: soil moisture (v/v)
    """
    if np.max(ep)>70 or np.min(ep)<2:
        warnings.warn("input ep is less than 2 or greater than 70, replacing with nan!")
        try:
            ep[ep>70] = np.nan
            ep[ep<2] = np.nan
        except:
            ep = np.nan
        
    mv = (-530+292*ep-5.5*ep**2+0.043*ep**3)*1e-4    
    
    return mv


def mv2ep(mv):
    """
    this function converts the soil moisture into 
    the real part of dielectric constant

    this uses the function ep2mv and invert it usign the LUT    
    
    Input:
        mv: soil moisture (v/v)
    Output:
        ep: real part of the dielectric constant
    """
    ep_lut = np.linspace(2,70)
    mv_lut = ep2mv(ep_lut)
    f = interp1d(mv_lut, ep_lut, bounds_error=False, fill_value=np.nan)
    ep = f(mv)
    return ep


def hallikainen_ep(mv, S, C, fre, imaginary=False):
    """
    Ref: HALLIKAINEN et al.: MICROWAVE DIELECTRIC BEHAVIOR OF WET SOIL-PART I
    soil particles of diameters d>0.005 as sand, 
    0.002 mm < d < 0.05 mm as silt, 
    and d < 0.002 mm as clay.
    
    Input:
        mv: soil moisture (v/v)
        S: Sand percentage
        C: Clay percentage
        fre: frequeny (GHz)
    
    
    """
    frequencies = [1.4, 4, 6, 8, 10, 12, 14, 16, 18] #GHz
    
    a0 = [2.862, 2.927, 1.993, 1.997, 2.502, 2.200, 2.301, 2.237, 1.912]
    a1 = [-0.012, -0.012, 0.002, 0.002, -0.003, -0.001, 0.001, 0.002, 0.007]
    a2 = [0.001, -0.001, 0.015, 0.018, -0.003, 0.012, 0.009, 0.009, 0.021]
    
    b0 = [3.803, 5.505, 38.086, 25.579, 10.101, 26.473, 17.918, 15.505, 29.123]
    b1 = [0.462, 0.371, -0.176, -0.017, 0.221, 0.013, 0.084, 0.076, -0.190]
    b2 = [-0.341, 0.062, -0.633, -0.412, -0.004, -0.523, -0.282, -0.217, -0.545]
    
    c0 = [119.006, 114.826, 10.720, 39.793, 77.482, 34.333, 50.149, 48.260, 6.960]
    c1 = [-0.500, -0.389, 1.256, 0.723, -0.061, 0.284, 0.012, 0.168, 0.822]
    c2 = [0.633, -0.547, 1.522, 0.941, -0.135, 1.062, 0.387, 0.289, 1.195]

    
    coeffs = ['a0', 'a1', 'a2', 'b0', 'b1', 'b2', 'c0', 'c1', 'c2']
    for coeff in coeffs:
        exec("f_%s = interp1d(frequencies, %s, bounds_error=False, fill_value=np.nan)"%(coeff,coeff))
    
    a = f_a0(fre) + f_a1(fre)*S + f_a2(fre)*C
    b = f_b0(fre) + f_b1(fre)*S + f_b2(fre)*C
    c = f_c0(fre) + f_c1(fre)*S + f_c2(fre)*C
    
    ep = a + b*mv + c*mv**2     
    
    
    ######################### imaginary part ##################################
    if imaginary:
        a0 = [0.356, 0.004, -0.123, -0.201, -0.070, -0.142, -0.096, -0.027, -0.071]
        a1 = [-0.003, 0.001, 0.002, 0.003, 0.000, 0.001, 0.001, -0.001, 0.000]
        a2 = [-0.008, 0.002, 0.003, 0.003, 0.001,  0.003, 0.002, 0.003, 0.003]
        
        b0 = [5.507, 0.951, 7.502, 11.266, 6.620, 11.868, 8.583, 6.179, 6.938]
        b1 = [0.044, 0.005, -0.058, -0.085, 0.015, -0.059, -0.005, 0.074, 0.029]
        b2 = [-0.002, -0.010, -0.116, -0.155, -0.081, -0.225, -0.153, -0.086, -0.128]
        
        c0 = [17.753, 16.759, 2.942, 0.194, 21.578, 7.817, 28.707, 34.126, 29.945]
        c1 = [-0.313, 0.192, 0.452, 0.584, 0.293,  0.570, 0.297, 0.143, 0.275]
        c2 = [0.206, 0.290, 0.543, 0.581, 0.332,  0.801, 0.357, 0.206, 0.377]

    
        coeffs = ['a0', 'a1', 'a2', 'b0', 'b1', 'b2', 'c0', 'c1', 'c2']
        for coeff in coeffs:
            exec("f_%s = interp1d(frequencies, %s, bounds_error=False, fill_value=np.nan)"%(coeff,coeff))
    
        a = f_a0(fre) + f_a1(fre)*S + f_a2(fre)*C
        b = f_b0(fre) + f_b1(fre)*S + f_b2(fre)*C
        c = f_c0(fre) + f_c1(fre)*S + f_c2(fre)*C
    
        ep_i = a + b*mv + c*mv**2   
        
        ep = np.complex(ep, ep_i)
    
    return ep



def hallikainen_mv(ep, S, C, fre):
    """
    Ref: HALLIKAINEN et al.: MICROWAVE DIELECTRIC BEHAVIOR OF WET SOIL-PART I
    soil particles of diameters d>0.005 as sand, 
    0.002 mm < d < 0.05 mm as silt, 
    and d < 0.002 mm as clay.
    
    Input:
        ep: real part of the dielectric constant 
        S: Sand percentage
        C: Clay percentage
        fre: frequeny (GHz)
    Output:
        mv: Soil moisture (v/v)   
    
    """
    frequencies = [1.4, 4, 6, 8, 10, 12, 14, 16, 18] #GHz
    
    a0 = [2.862, 2.927, 1.993, 1.997, 2.502, 2.200, 2.301, 2.237, 1.912]
    a1 = [-0.012, -0.012, 0.002, 0.002, -0.003, -0.001, 0.001, 0.002, 0.007]
    a2 = [0.001, -0.001, 0.015, 0.018, -0.003, 0.012, 0.009, 0.009, 0.021]
    
    b0 = [3.803, 5.505, 38.086, 25.579, 10.101, 26.473, 17.918, 15.505, 29.123]
    b1 = [0.462, 0.371, -0.176, -0.017, 0.221, 0.013, 0.084, 0.076, -0.190]
    b2 = [-0.341, 0.062, -0.633, -0.412, -0.004, -0.523, -0.282, -0.217, -0.545]
    
    c0 = [119.006, 114.826, 10.720, 39.793, 77.482, 34.333, 50.149, 48.260, 6.960]
    c1 = [-0.500, -0.389, 1.256, 0.723, -0.061, 0.284, 0.012, 0.168, 0.822]
    c2 = [0.633, -0.547, 1.522, 0.941, -0.135, 1.062, 0.387, 0.289, 1.195]

    
    coeffs = ['a0', 'a1', 'a2', 'b0', 'b1', 'b2', 'c0', 'c1', 'c2']
    for coeff in coeffs:
        exec("f_%s = interp1d(frequencies, %s, bounds_error=False, fill_value=np.nan)"%(coeff,coeff))
    
    a = f_a0(fre) + f_a1(fre)*S + f_a2(fre)*C
    b = f_b0(fre) + f_b1(fre)*S + f_b2(fre)*C
    c = f_c0(fre) + f_c1(fre)*S + f_c2(fre)*C
    
    #c*mv**2 + b*mv + a-ep  = 0
    mv = (-b + np.sqrt(b**2-4*c*(a-ep)))/(2*c)
    #mv = (-b - np.sqrt(b**2-4*c*(a-ep)))/(a*c)
        
    return mv

    
if __name__ == "__main__":
    s = [51.51, 41.96, 30.63, 17.16, 5.02]
    c = [13.43, 8.53, 13.48, 19.00, 47.38]
    mv = np.linspace(0,0.55)
    ep = np.empty((5,50))
    for i in range(5):
        ep[i] = hallikainen_ep(mv, s[i], c[i], 1.4)
    
    #plt.plot(mv, ep.T)
    #plt.show()
    
    # check for inverse
    mv_computed = np.empty((5,50))
    for i in range(5):
        mv_computed[i] = hallikainen_mv(ep[i], s[i], c[i], 1.4)
        
        plt.scatter(mv_computed[i], mv)
    plt.show()
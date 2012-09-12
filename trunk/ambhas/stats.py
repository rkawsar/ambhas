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
from scipy.stats import norm, chi2
from scipy.stats import scoreatpercentile

def bias_correction(oc, mc, mp, nonzero = True):
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
    if nonzero:
        OC[OC<0] = 0
        
    f = interp1d(F_oc, OC)
    
    F1 = st.cpdf(mc, mp)
    mp_adjusted = f(F1)
    
    if nonzero:
        mp_adjusted[mp_adjusted>0] = mp_adjusted[mp_adjusted>0] + np.sum(
        mp_adjusted[mp_adjusted<0])/(np.sum(mp_adjusted>0))
        mp_adjusted[mp_adjusted<0] = 0
        
    return mp_adjusted


def mk_test(x, alpha = 0.05):
    """
    this perform the MK (Mann-Kendall) test to check if there is any trend present in 
    data or not
    
    Input:
        x:   a vector of data
        alpha: significance level
    
    Output:
        trend: tells the trend (increasing, decreasing or no trend)
        h: True (if trend is present) or False (if trend is absence)
        p: p value of the sifnificance test
        z: normalized test statistics 
        
    Examples
    --------
      >>> x = np.random.rand(100)
      >>> trend,h,p,z = mk_test(x,0.05) 
    """
    n = len(x)
    
    # calculate S 
    s = 0
    for k in xrange(n-1):
        for j in xrange(k+1,n):
            s += np.sign(x[j] - x[k])
    
    # calculate the unique data
    unique_x = np.unique(x)
    g = len(unique_x)
    
    # calculate the var(s)
    if n == g: # there is no tie
        var_s = (n*(n-1)*(2*n+5))/18
    else: # there are some ties in data
        tp = np.zeros(unique_x.shape)
        for i in xrange(len(unique_x)):
            tp[i] = sum(unique_x[i] == x)
        var_s = (n*(n-1)*(2*n+5) + np.sum(tp*(tp-1)*(2*tp+5)))/18
    
    if s>0:
        z = (s - 1)/np.sqrt(var_s)
    elif s == 0:
            z = 0
    elif s<0:
        z = (s + 1)/np.sqrt(var_s)
    
    # calculate the p_value
    p = 2*(1-norm.cdf(abs(z))) # two tail test
    h = abs(z) > norm.ppf(1-alpha/2) 
    
    if (z<0) and h:
        trend = 'decreasing'
    elif (z>0) and h:
        trend = 'increasing'
    else:
        trend = 'no trend'
        
    return trend, h, p, z

def independant(x,y, alpha = 0.05):
    """
    this program calculates check if the joint cdf == multiplication of marginal
    distribution or not 
    using the chi-squared test 
        
    Input:
        x:   a vector of data
        y:   a vector of data
        alpha: significance level
    
    Output:
        ind: True (if independant) False (if dependant)
        p: p value of the significance test
        
    Examples
    --------
      >>> x = np.random.rand(100)
      >>> y = np.random.rand(100)
      >>> ind,p = independant(x,y,0.05)  
    """
    
    # calculate the 2D histogram 
    H, xedges, yedges = np.histogram2d(x, y, bins=5)
    
    # calculate the expected values
    expected_values = np.zeros(H.shape)
    for i in range(H.shape[0]):
        for j in range(H.shape[1]):
            expected_values[i,j] = H.sum(axis=1)[i]*H.sum(axis=0)[j]/H.sum()
    
    # calculate the chi-squared statistics
    err_chi2 = ((H-expected_values)**2/expected_values).sum()
    
    # degree of freedom
    dof = (H.shape[0]-1)*(H.shape[1]-1)
    
    # calculate the p_value
    rv = chi2(dof)
    p = 2*(1-rv.sf(err_chi2)) # two tail test
    
    # test 
    ind = p >= alpha        
        
    return ind, p


class SpatOutlier():
    """
    this class identify the outliers from the given spatial data of point values
    """
    
    def __init__(self,rain):
        """
        Input:
            rain:   rain at different spatial locations and time
            time ==> is defined in the first dimension
            space ==> is defined in the second dimension
        """
        # check for the number of dimension
        if rain.ndim > 2:
            raise ValueError('The dimension of the input should be less than or equal to 2 (two)')
        elif rain.ndim == 1:
            rain.shape = (1,-1)
        self.rain = rain
            
    def _identify_outlier(self,threshold=2.0):
        """
        Input:
            threshold: threshold above which the data will be termed as outlier
        """
        rain = self.rain
        q_25 = scoreatpercentile(rain.T,25)
        q_75 = scoreatpercentile(rain.T,75)
        q_50 = scoreatpercentile(rain.T,50)
        
        q_25_m = np.tile(q_25,(rain.shape[1],1)).T
        q_50_m = np.tile(q_50,(rain.shape[1],1)).T
        q_75_m = np.tile(q_75,(rain.shape[1],1)).T
        
        index = np.abs(rain-q_50_m)/(q_75_m-q_25_m)
        self.index = index
        
        self.outliers = index>=threshold
    
    def fill_with_nan(self):
        """
        this method fills the outliers with the nan
        
        Output:
            rain_filled:    rain filled with nan where outliers were present
        """
        self._identify_outlier()
        
        rain_filled = self.rain
        rain_filled[self.outliers] = np.nan
        return rain_filled

if __name__ == "__main__":
    oc = np.random.randn(100)
    mc = 2+np.random.randn(100)
    mp = 2+np.random.randn(1000)
    
    print("mean of observed current is %f"%oc.mean())
    print("mean of modeled current is %f"%mc.mean())
    print("mean of modeled prediction is %f"%mp.mean())
     
    mp_adjusted = bias_correction(oc, mc, mp)
    print("mean of adjusted modeled prediction is %f"%mp_adjusted.mean())
    
    # check the SpatOutlier class
    x = np.random.randn(5,20)
    x[4,4] = 2.9
    foo = SpatOutlier(x)
    x1 = foo.fill_with_nan()
    print x1[4,4]

    

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 18 17:11:48 2014

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

Python binding for the copula function from R using Rpy.
"""

from __future__ import division

import numpy as np
import statistics as st
from scipy.interpolate import interp1d
from scipy.stats import kendalltau, pearsonr, spearmanr
from stats import scoreatpercentile

from rpy2.robjects import r
import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()
r("library('copula')")

class Copula():
    """
    This class estimate parameter of copula
    generate joint random variable for the parameters
    This class has following three copulas:
        Clayton
        Frank
        Gumbel
        
    Example:
        x = np.random.normal(size=20)
        y = np.random.normal(size=20)
        foo = Copula(x, y, 'frank')
        u,v = foo.generate_uv(1000)
    """
    

    def __init__(self, X, Y, family):
        """ initialise the class with X and Y
        Input:
            X:        one dimensional numpy array
            Y:        one dimensional numpy array
            family:   clayton or frank or gumbel
            
            Note: the size of X and Y should be same
        """
        # check dimension of input arrays
        if not ((X.ndim==1) and (Y.ndim==1)):
            raise ValueError('The dimension of array should be one.')
        
        # input array should have same size
        if X.size != Y.size:
            raise ValueError('The size of both array should be same.')
        
        # check if the name of copula family correct
        copula_family = ['clayton', 'frank', 'gumbel']
        if family not in copula_family:
            raise ValueError('The family should be clayton or frank or gumbel')
        
        self.X = X
        self.Y = Y
        self.family = family
        
        # estimate Kendall'rank correlation
        xy = np.vstack([X,Y])
        r.assign('xy',xy.T)
        tau = r('tau. <- cor(xy, method="kendall")[1,2]')[0]
        self.xy = xy
        self.tau = tau          
        
        # estimate pearson R and spearman R
        self.pr = r('cor(xy, method="pearson")[1,2]')[0]
        self.sr = r('cor(xy, method="spearman")[1,2]')[0]
                
        # estimate the parameter of copula
        self._get_parameter()
        
        # set U and V to none
        self.U = None
        self.V = None
        
        
    def _get_parameter(self):
        """ estimate the parameter (theta) of copula
        """     
        r.assign('tau.',self.tau)
        
        if self.family == 'clayton':
            self.theta = r('iTau(claytonCopula(), tau.)')[0]
            
        elif self.family == 'frank':
            self.theta = r('iTau(frankCopula(), tau.)')[0]
            
        elif self.family == 'gumbel':
            self.theta = r('iTau(gumbelCopula(), tau.)')[0]
    
    def generate_uv(self, n=1000):
        """
        Generate random variables (u,v)
        
        Input:
            n:        number of random copula to be generated
        
        Output:
            U and V:  generated copula
            
        """
        # CLAYTON copula
        if self.family == 'clayton':
            UV = np.array(r('rCopula(%d, claytonCopula(%f))'%(n,self.theta)))
            
        # FRANK copula
        elif self.family == 'frank':
            UV = np.array(r('rCopula(%d, frankCopula(%f))'%(n,self.theta)))
            
        # GUMBEL copula
        elif self.family == 'gumbel':
            UV = np.array(r('rCopula(%d, gumbelCopula(%f))'%(n,self.theta)))
            
        self.U = UV[:,0]
        self.V = UV[:,1]
        return self.U, self.V
    
    def generate_xy(self, n=1000):
        """
        Generate random variables (x, y)
        
        Input:
            n:        number of random copula to be generated
        
        Output:
            X1 and Y1:  generated copula random numbers
            
        """
        # if U and V are not already generated
        if self.U is None:
            self.generate_uv(n)
            
        # estimate inverse cdf of x and y
        self._inverse_cdf()
        
        # estimate X1 and Y1        
        X1 = self._inv_cdf_x(self.U)
        Y1 = self._inv_cdf_y(self.V)
        self.X1 = X1
        self.Y1 = Y1
        
        return X1, Y1

    def _inverse_cdf(self):
        """
        This module will calculate the inverse of CDF 
        which will be used in getting the ensemble of X and Y from
        the ensemble of U and V
        
        The statistics module is used to estimate the CDF, which uses
        kernel methold of cdf estimation
        
        To estimate the inverse of CDF, interpolation method is used, first cdf 
        is estimated at 100 points, now interpolation function is generated 
        to relate cdf at 100 points to data
        """
        x2, x1 = st.cpdf(self.X, kernel = 'Epanechnikov', n = 100)
        self._inv_cdf_x = interp1d(x2, x1)
        
        y2, y1 = st.cpdf(self.Y, kernel = 'Epanechnikov', n = 100)
        self._inv_cdf_y = interp1d(y2, y1)


    def estimate(self, data=None):
        """
        this function estimates the mean, std, iqr for the generated
        ensemble

        Output:
            Y1_mean = mean of the simulated ensemble
            Y1_std = std of the simulated ensemble
            Y1_ll = lower limit of the simulated ensemble
            Y1_ul = upper limit of the simulated ensemble
        """
        nbin = 50
        #check if already the generate_xy has been called,
        #if not called, call now
        try:
            self.X1
            copula_ens = len(self.X1)
        except:
            copula_ens = 10000
            self.generate_xy(copula_ens)
        
        if data is None:
            data = self.X
        
        n_ens = copula_ens/nbin #average no. of bin in each class
        ind_sort = self.X1.argsort()
        x_mean = np.zeros((nbin,))
        y_mean = np.zeros((nbin,))
        y_ul = np.zeros((nbin,))
        y_ll = np.zeros((nbin,))
        y_std = np.zeros((nbin,))
    
        for ii in range(nbin):
            x_mean[ii] = self.X1[ind_sort[n_ens*ii:n_ens*(ii+1)]].mean()
            y_mean[ii] = self.Y1[ind_sort[n_ens*ii:n_ens*(ii+1)]].mean()
            y_std[ii] = self.Y1[ind_sort[n_ens*ii:n_ens*(ii+1)]].std()
            y_ll[ii] = scoreatpercentile(self.Y1[ind_sort[n_ens*ii:n_ens*(ii+1)]], 25)
            y_ul[ii] = scoreatpercentile(self.Y1[ind_sort[n_ens*ii:n_ens*(ii+1)]], 75)
            
        foo_mean = interp1d(x_mean, y_mean, bounds_error=False)
        foo_std = interp1d(x_mean, y_std, bounds_error=False)
        foo_ll = interp1d(x_mean, y_ll, bounds_error=False)
        foo_ul = interp1d(x_mean, y_ul, bounds_error=False)
        
        
        Y1_mean = foo_mean(data)
        Y1_std = foo_std(data)
        Y1_ll = foo_ll(data)
        Y1_ul = foo_ul(data)
        
        return Y1_mean, Y1_std, Y1_ll, Y1_ul
    
    
    def estimate_ens(self, data=None, pc=[50]):
        """
        this function estimates the scoreatpercentile for the generated
        ensemble

        Output:
            Y1_pc = score at percentile for the ismulated ensemble
        """
        n_pc = len(pc)
        nbin = 50
        #check if already the generate_xy has been called,
        #if not called, call now
        try:
            self.X1
            copula_ens = len(self.X1)
        except:
            copula_ens = 10000
            self.generate_xy(copula_ens)
        
        if data is None:
            data = self.X
        
        n_ens = copula_ens/nbin #average no. of bin in each class
        ind_sort = self.X1.argsort()
        x_mean = np.zeros((nbin,))
        y_pc = np.zeros((nbin,n_pc))
            
        for ii in range(nbin):
            x_mean[ii] = self.X1[ind_sort[n_ens*ii:n_ens*(ii+1)]].mean()
            for jj in range(n_pc):
                y_pc[ii,jj] = scoreatpercentile(self.Y1[ind_sort[n_ens*ii:n_ens*(ii+1)]], pc[jj])
        
        
        Y1_pc = np.zeros((len(data),n_pc))
        for jj in range(n_pc):
            foo_pc = interp1d(x_mean, y_pc[:,jj], bounds_error=False)
            Y1_pc[:,jj] = foo_pc(data)
            
        return Y1_pc
        
    def gof(self, method='Sn', simulation='pb'):
        """
        Goodness-of-fit tests for copulas 
        gofCopula from the R copula package
        
        Input:
            method: "Sn" -> test statistic from Genest, Rémillard, Beaudoin (2009)
                    "SnB"-> test statistic from Genest, Rémillard, Beaudoin (2009)
                    "SnC" -> test statistic from Genest et al. (2009).
                    "AnChisq" -> Anderson-Darling test statistic
                    "AnGamma -> similar to "AnChisq" but based on the gamma distribution 
            simulation: "pb" -> parametric bootstrap
                        "mult" -> multiplier
        Output:
            
        """
        xy = self.xy
        r.assign('xy',xy.T)
        theta = self.theta
        r('foo <- gofCopula(claytonCopula(%f), xy, estim.method="itau", method="%s", simulation="%s")'%(theta,method,simulation))
        p_value = float(r('foo$p.value')[0])
        statistic = float(r('foo$statistic')[0])
        parameter = float(r('foo$parameter')[0])
        
        self.p_value = p_value
        self.statistic = statistic 
        self.parameter = parameter
        
        return statistic, p_value, parameter


if __name__ == '__main__':
    x = np.random.normal(size=20)
    y = 1.5*x+np.random.normal(size=20)
    #foo = Copula(x, y, 'frank')
    foo = Copula(x,y, 'gumbel')
    #u,v = foo.generate_uv()
    #x1,y1 = foo.generate_xy()
    foo.gof(method='SnC')
    
    
    


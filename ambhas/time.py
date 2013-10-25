#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 11:55:12 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

import datetime as dt
import numpy as np

def ymd2doy(year, month, day):
    n = len(year)
    doy = np.empty(n, int)
    for i in xrange(n):
        doy[i] = dt.datetime(year[i], month[i], day[i]).toordinal()-dt.datetime(year[i], 1, 1).toordinal()+1
    return doy

def doy2md(doy,year):
    foo = dt.date.fromordinal(dt.date(year,1,1).toordinal()+doy-1)
    month = foo.month
    day = foo.day
    return month,day
    
    

if __name__=='__main__':
    year = 2011
    doy = 365
    print doy2md(doy,year)
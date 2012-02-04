# -*- coding: utf-8 -*-
"""
Created on Fri Feb 03 18:12:26 2012

@author: K. Sreelash
@website: www.ambhas.com
@email: satkumartomer@gmail.com
"""

# import required libraries
from __future__ import division
import numpy as np
from ambhas.xls import xlsread



#input
infile_name = 'D:/svn/ambhas/examples/input_stics.xls'


# read the parameters
xls_file = xlsread(infile_name)

# soil par
argis = xls_file.get_cells('B2', 'soil_par')
norgs = xls_file.get_cells('C2', 'soil_par')
                                                                                        
# plant par
# tech par
# climate

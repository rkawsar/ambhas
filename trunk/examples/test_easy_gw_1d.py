# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 15:22:21 2012

@author: Sat Kumar Tomer
@website: www.ambhas.com
@email: satkumartomer@gmail.com
"""

from ambhas.easy_gw_1d import gw_model_file

# define the name of data files
in_fname = '/home/tomer/svn/ambhas/examples/input_gw.xls'
out_fname = '/home/tomer/Persons/madhu/output_gw.xls'
figure_dir = '/home/tomer/Persons/madhu/'

gw_model_file(in_fname, out_fname, figure_dir)
## if you dont want figure, then uncomment the following line
#gw_model_file(in_fname, out_fname)
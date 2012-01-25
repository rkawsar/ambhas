# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 13:30:46 2012

@author: Sat Kumar Tomer
@website: www.ambhas.com
@email: satkumartomer@gmail.com

this module reads the data from xls file
perform the lumped grounwater level modelling
then save the output as xls file and images
"""

import numpy as np
import matplotlib.pyplot as plt
import xlrd, xlwt
from ambhas.gw import GW_1D
import scikits.timeseries as ts
import scikits.timeseries.lib.plotlib as tpl


def gw_model_file(in_fname, out_fname, figure_dir=None):
    """"
    input:
        in_fname:   name of input xls file
        out_fname:  name of the output xls file
        figure_dir: name of the directory where to save the out figures
    """

    # read the data from xls file
    in_book = xlrd.open_workbook(in_fname)
    sheet_names = in_book.sheet_names()
    sheet_names.remove('legend')
    
    out_book = xlwt.Workbook()
    for sheet_name in sheet_names:
    
        sheet = in_book.sheet_by_name(sheet_name)
        # read the input for one well
        t = sheet.nrows-1
        year = np.empty(t, 'int')
        month = np.empty(t, 'int')
        rainfall = np.empty(t)
        pumping = np.empty(t)
        meas_gwl = np.empty(t)
        r = np.empty(t)
        for i in range(t):
            year[i] = sheet.cell_value(i+1,0)
            month[i] = sheet.cell_value(i+1,1)
            rainfall[i] = sheet.cell_value(i+1,2)
            pumping[i] = sheet.cell_value(i+1,3)
            meas_gwl[i] = sheet.cell_value(i+1,4)
            r[i] = sheet.cell_value(i+1,5)
        F = sheet.cell_value(1,6)
        G = sheet.cell_value(1,7)
        hmin = sheet.cell_value(1,8)
        
        # run the model
        gw_model = GW_1D(rainfall, pumping)
        gw_model.set_parameters(F, G, r, hmin)
        
        hini = meas_gwl[0]
        gw_model.run_model(hini,t)
        sim_gwl = gw_model.h
        lam = gw_model.lam
        sy = gw_model.sy
        discharge = gw_model.discharge
        
        #write the output
        sheet = out_book.add_sheet(sheet_name)
        sheet.write(0,0,'year')
        sheet.write(0,1,'month')
        sheet.write(0,2,'rainfall')
        sheet.write(0,3,'pumping')
        sheet.write(0,4,'measured gwl')
        sheet.write(0,5,'simulated gwl')
        sheet.write(0,6,'recharge')
        sheet.write(0,7,'discharge')
        sheet.write(0,8,'lambda')
        sheet.write(0,9,'sy')
        for i in range(t):
            sheet.write(i+1,0,year[i])
            sheet.write(i+1,1,month[i])
            sheet.write(i+1,2,rainfall[i])
            sheet.write(i+1,3,pumping[i])
            sheet.write(i+1,4,meas_gwl[i])
            sheet.write(i+1,5,sim_gwl[i])
            sheet.write(i+1,6,rainfall[i]*r[i])
            sheet.write(i+1,7,discharge[i])
        sheet.write(1,8,lam)
        sheet.write(1,9,sy)
            
        first_date = ts.Date(freq='M',year=year[0],month=month[1])
        gw_meas_series = ts.time_series(meas_gwl, start_date=first_date)
        gw_sim_series = ts.time_series(sim_gwl, start_date=first_date)
        
        if figure_dir is not None:
            # save the figure
            fig = tpl.tsfigure()
            fsp = fig.add_tsplot(111)
            fsp.tsplot(gw_meas_series, 'r', lw=3, label='measured')
            fsp.tsplot(gw_sim_series, 'g', lw=3, label='simulated')
            fsp.legend(loc='best')
            plt.ylabel('Groundwater Level' )
            plt.savefig(figure_dir+'%s.png'%sheet_name)
            plt.close()
        
        print('%s completed succesfully'%sheet_name)
    
    # save the xls file
    out_book.save(out_fname)

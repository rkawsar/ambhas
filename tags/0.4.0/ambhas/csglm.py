# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 19:58:19 2011

@author: Sat Kumar Tomer
@website: www.ambhas.com
@email: satkumartomer@gmail.com

Copuled Surface-Ground water Lumped hydrological Model
"""

from __future__ import division
# import required modules
import numpy as np
import xlrd, xlwt
import os
import gdal
from gdalconst import *
from scipy.interpolate import Rbf
from Scientific.IO import NetCDF as nc
import datetime
np.seterr(all='raise')

class CSGLM:
    """
    This is the main class of the CGLSM.
    This will read the input data,
    do the processing
    and then write the output files
    
    """
    
    
    def __init__(self, input_file):
        """
        Input:
            input_file: the file which contains all the information
            including forcing and parameters.
        """        
        
        self.input_file = input_file
        
        # read the input data
        self._read_input()
        
        ################ run the model ########################
        max_t = int(self.final_time/self.dt)
        self.max_t = max_t
        # initialize required variables
        # the length of state variables (i.e. soil moisture and gw level) is
        # one more than the timesteps
        self.actual_evap = np.empty(max_t)
        self.actual_trans = np.empty(max_t)    
        self.E_In = np.empty(max_t)    
        self.horton_runoff = np.empty(max_t)    
        self.recharge = np.empty(max_t)    
        self.runoff = np.empty(max_t)    
        self.gw_level = np.empty(max_t+1) 
        self.gw_level[0] = self.initial_gwl
        self.sm = np.empty((self.no_layer,max_t+1))
        self.sm[:,0] = self.initial_sm.flatten()
        self.surface_storage = np.zeros(max_t+1)
        
        for t in range(max_t):
            self.t = t
              
            # get forcing data at current time step        
            self._get_forcing()
            
            # call the interception module
            self._interception_fun()
            
            # call the runoff module
            self._runoff_fun()
            
            # call the soil module
            self._soil_fun()
            
            # call the surface storage module
            self._surface_storage_fun()
            
            # call the goundwater module
            self._gw_fun()
        
        # write the output
        self._write_output()

    def _read_input(self):
        """
        This checks if all the required input sheets are present in the xls file,
        read the data from input file, which can be used later in other functions
        """
    
        # list of required files in the input directory
        input_sheets = ['ind', 'forcing', 'initial_condition', 'gw_par',
                       'runoff_par', 'units', 'root_info', 'temporal_info',
                       'spatial_info', 'ET_par', 'soil_hyd_par', 'output_par']
        
        # check if all the required sheets are present or not
        self._check_sheets(input_sheets, self.input_file)
        
        # read the legend
        self._read_ind()
        
        # read the spatial data
        self._read_spatial()
        
        # read the temporal data
        self._read_temporal()

        # read the root distribution data
        self._read_root_distribution()
        
        # read the units 
        self._read_units()
        
        # read the initial condition
        self._read_initial_condition()
        
        # read the soil hydraulic properties data
        self._read_shp()
        
        # read the parameters related to runoff
        self._read_runoff_par()
        
        # read the parameters related to surface storage
        self._surface_storage_par()
        
        # read the groundwaer parameters data
        self._read_gw_par()
        
        # read the ET parameter data
        self._read_ET_par()
        
        # read the forcing infomation
        self._read_forcing()
        
        # read the outfile name
        self._read_ofile_name()
        
        # print the reading status
        output_message = 'Input data reading completed sucessfully'
        self._colored_output(output_message, 32)
       
    def _check_sheets(self, check_sheets, check_file):
        """
        This functions check if all the sheets needed to model are present  
        in check_file
        
        """
        # open the xls file and get its sheets
        foo = xlrd.open_workbook(check_file)
        check_sheet_names = foo.sheet_names()
        
        for check_sheet_names in check_file:
            if check_sheet_names not in check_file:
                output_message = check_sheet_names + ' is missing'
                self._colored_output(output_message,31)

    def _read_ind(self):
        """
        Read the ind sheet
        legend stores the information about the indices of other properties,
        which would be used by all other properties reading functions
        """
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('ind')
        # dont read the first line of the xls file
        ind = {}
        for i in range(sheet.nrows-1):
            ind[str(sheet.cell_value(i+1,0))] = int(sheet.cell_value(i+1,1))
                
        self.ind = ind

    def _read_spatial(self):
        """
        Read the spatial info
        """
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('spatial_info')
        # get the row number from the ind
        j = self.ind['spatial_info']
        no_layer = int(sheet.cell_value(j,1))
        z = sheet.row_values(j,2)
        if no_layer != len(z):
            raise ValueError('The length of the thickness_layers\
            should be equal to the No_layer')
        
        self.no_layer = no_layer
        self.z = z
        #mid depth of the layers
        depth = np.zeros(no_layer+1)
        depth[1:] = np.cumsum(z)
        self.mid_z = 0.5*(depth[1:]+depth[:-1])
        
    
    def _read_temporal(self):
        """
        Read the temporal info
        """
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('temporal_info')
        #get the row number from the ind
        j = self.ind['temporal_info']
        dt = sheet.cell_value(j,1)
        final_time = sheet.cell_value(j,2)
        
        self.dt = dt
        self.final_time = final_time
    
    def _read_root_distribution(self):
        """
        read the root distribution factors
        """
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('root_info')
        #get the row number from the ind
        j = self.ind['root_info']
        self.ndvi_max = sheet.cell_value(j,1)
        self.ndvi_min = sheet.cell_value(j,2)
        self.fapar_max = sheet.cell_value(j,3)
        self.lai_max = sheet.cell_value(j,4)
        self.Rd_max = sheet.cell_value(j,5)
        self.Lrd = sheet.cell_value(j,6)
  
            
    def _read_units(self):
        """
        read the units of the forcing data
        """
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('units')
        #get the row number from the ind
        j = self.ind['units']
        forcing_units = {}
        for i in range(sheet.ncols-1):
            forcing_units[str(sheet.cell_value(0,i+1))] = str(sheet.cell_value(j,i+1))
        self.forcing_units = forcing_units
    
    def _read_initial_condition(self):
        """
        read initial condition
        """
        #get the row number from the ind
        j = self.ind['initial_condition']
        
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('initial_condition')
        theta_0 = sheet.row_values(j,2)
        self.initial_gwl = sheet.cell_value(j,1)
        self.initial_sm = np.array(theta_0)
        
        try:
            self.initial_sm.shape = self.no_layer,1
        except:
            raise ValueError('The length of the theta_0 should be \
            equal to the no_layer')
    
    def _read_shp(self):
        """
        read the soil hydraulic parameters
        """
        #get the row number from the ind
        j = self.ind['soil_hyd_par']
        
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('soil_hyd_par')
        soil_par = {}
        soil_par['qr'] = sheet.cell_value(j,1)
        soil_par['f'] = sheet.cell_value(j,2)
        soil_par['a'] = sheet.cell_value(j,3)
        soil_par['n'] = sheet.cell_value(j,4)
        soil_par['Ks'] = sheet.cell_value(j,5)
        soil_par['l'] = sheet.cell_value(j,6)
        #soil_par['evap_wp'] = sheet.cell_value(j,7)
        #soil_par['evap_fc'] = sheet.cell_value(j,8)
        soil_par['zl'] = sheet.cell_value(j,9)
        soil_par['fl'] = sheet.cell_value(j,10)
        
        m = 1-1/soil_par['n']
        # evaluate wilting point and field capacity
        soil_par['evap_fc'] = self.psi2theta(-0.33, soil_par['qr'], soil_par['f'], 
                               soil_par['a'], m, soil_par['n'])
        
        soil_par['evap_wp'] = self.psi2theta(-15, soil_par['qr'], soil_par['f'], 
                               soil_par['a'], m, soil_par['n'])
                               
        self.soil_par = soil_par
    
    def psi2theta(self,psi, thetar, thetas, alpha, m, n):
         """
         psi2theta: given the theta calculate the pressure head
         """
         if (psi>=0):
             theta = thetas
         elif psi<-1e6:
             theta = 1.01*thetar
         else:
             theta = thetar+(thetas-thetar)*pow(1+pow(abs(alpha*psi),n),-m)
         return theta
         
    def _read_runoff_par(self):
        """
        read the parameters related to runoff
        """
        #get the row number from the ind
        j = self.ind['runoff_par']
        
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('runoff_par')
        runoff_par = {}
        for i in range(sheet.ncols-1):
            runoff_par[str(sheet.cell_value(0,i+1))] = float(sheet.cell_value(j,i+1))
        self.runoff_par = runoff_par
    
    def _surface_storage_par(self):
        """
        read the parameters related to surface storage
        """
        #get the row number from the ind
        j = self.ind['surface_storage_par']
        
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('surface_storage_par')
        surface_storage_par = {}
        surface_storage_par['a'] = float(sheet.cell_value(j,1))
        surface_storage_par['b'] = float(sheet.cell_value(j,2))
        self.surface_storage_par = surface_storage_par
    
    def _read_gw_par(self):
        """
        read the parameters related to groundwater
        """        
        #get the row number from the ind
        j = self.ind['gw_par']
        
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('gw_par')
        gw_par = {}
        for i in range(sheet.ncols-1):
            gw_par[str(sheet.cell_value(0,i+1))] = float(sheet.cell_value(j,i+1))
        
        self.gw_par = gw_par
    
    def _read_ET_par(self):
        """
        read the parameters related to evaporation
        """
        #get the row number from the ind
        #j = self.ind['ET_par']
        
        #book = xlrd.open_workbook(self.input_file)
        #sheet = book.sheet_by_name('ET_par')
        ET_par = {}
        #ET_par['trans_fc'] = sheet.cell_value(j,1)
        #ET_par['trans_wp'] = sheet.cell_value(j,2)
        qr = self.soil_par['qr']
        f = self.soil_par['f']
        a = self.soil_par['a']
        n = self.soil_par['n']
        m = 1-1/n
        fl = self.soil_par['fl']
        mid_z = self.mid_z
        ET_par['trans_fc'] = self.psi2theta(-0.33, qr, f, a, m, n)*np.exp(-mid_z/fl)
        ET_par['trans_wp'] = self.psi2theta(-15, qr, f, a, m, n)*np.exp(-mid_z/fl)
        
        self.ET_par = ET_par
    
    def _read_forcing(self):
        """
        read the forcing data from xls file
        """
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('forcing')
        
        data_len = sheet.nrows-1
        year = np.zeros(data_len)
        doy = np.zeros(data_len)
        rain = np.zeros(data_len)
        pet = np.zeros(data_len)
        ndvi = np.zeros(data_len)
        pumping = np.zeros(data_len)
    
        for i in xrange(data_len):
            year[i] = sheet.cell_value(i+1,0)
            doy[i] = sheet.cell_value(i+1,1)
            rain[i] = sheet.cell_value(i+1,2)
            pet[i] = sheet.cell_value(i+1,3)
            ndvi[i] = sheet.cell_value(i+1,4)
            pumping[i] = sheet.cell_value(i+1,5)
        
        self.year = year
        self.doy = doy
        
        # if forcing data was in mm units, covert into m
        if self.forcing_units['rain'] == 'mm':
            self.rain = rain/1000.0
        elif self.forcing_units['rain'] == 'm':
            self.rain = rain
        else:
            raise ValueError("The units of rain should be either 'mm' or 'm' ")

        if self.forcing_units['pet'] == 'mm':
            self.pet = pet/1000.0
        elif self.forcing_units['pet'] == 'm':
            self.pet = pet
        else:
            raise ValueError("The units of PET should be either 'mm' or 'm' ")
            
        if self.forcing_units['pumping'] == 'mm':
            self.pumping = pumping/1000.0
        elif self.forcing_units['pumping'] == 'm':
            self.pumping = pumping
        else:
            raise ValueError("The units of pumping should be either 'mm' or 'm' ")
        
        # compute the fractional vegetation cover, rooting depth and lai
        ndvi_max = self.ndvi_max
        ndvi_min = self.ndvi_min
        ndvi[ndvi>ndvi_max] = ndvi_max
        ndvi[ndvi<ndvi_min] = ndvi_min
        
        fapar = 1.60*ndvi-0.02
        fapar_max = self.fapar_max
        
        lai_max = self.lai_max
        lai = lai_max*np.log(1-fapar)/np.log(1-fapar_max)
        
        Rd_max = self.Rd_max  
        Rd = Rd_max*lai/lai_max
        fc = ((ndvi-ndvi_max)/(ndvi_max-ndvi_min))**2
        
        self.kc = 0.8+0.4*(1-np.exp(-0.7*lai))
        self.ndvi = ndvi
        self.lai = lai        
        self.Rd = Rd
        self.fc = fc
               

    def _read_ofile_name(self):
        """
        read the forcing data from xls file
        """
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('output_par')
        self.ofile_name = str(sheet.cell_value(0,1))


    def _colored_output(self, output_message, color):
        """
        This functions print  the output_message in the color
        Input:
            output_messgae: the text you want to print
            color: the color in which you want to print text, it could be one of:
                30: Gray
                31: Red
                32: Green
                33: Yellow
                34: Blue
                35: Magneta
                66: Cyan
                37: White
                38: Crimson
                41: Highlighted Red
                42: Highlighted Green 
                43: Highlighted Brown 
                44: Highlighted Blue 
                45: Highlighted Magenta 
                46: Highlighted Cyan
                47: Highlighted Gray 
                48: Highlighted Crimson 
        Output:
            This returns None, but print the output in python shell
        """
                
        print(("\033[31m" +output_message+ "\033[0m").replace('31',str(color)))

    def _get_forcing(self):
        """
        this will give the forcing at time t
        """
        # the PET is multiplied by crop coefficient
        self.rain_cur = self.rain[self.t]
        self.pet_cur = self.pet[self.t]*self.kc[self.t]
        self.lai_cur = self.lai[self.t]
        self.pumping_cur = self.pumping[self.t]
        
        self.cur_year = self.year[self.t]
        self.cur_doy = self.doy[self.t]

        
    def _interception_fun(self):
        """
        Input:
            lai_cur:    LAI at the current time step
            pet_cur:     PET at the current time step
            rain_cur:    Rainfall at the current time step
            
        Output:
            E_In:     Evaporation from Interception
            T:        Transpiration
            E:        Evaporation
            net_rain_cur:   Net rainfall (precipitation-interception loss) at 
            current time step
        """
        In = self.lai[self.t]*0.2/1000.0
        soil_cover = np.exp(-0.5*self.lai_cur)
        veg_cover = 1 - soil_cover
        
        E_In = np.min([veg_cover*self.rain_cur, veg_cover*self.pet_cur, veg_cover*In])
        T = np.min([veg_cover*self.pet_cur - 0.2*E_In, 1.2*self.pet_cur - E_In])
        E = np.min([soil_cover*self.pet_cur, 1.2*self.pet_cur-T-E_In])
        net_rain_cur = self.rain_cur - E_In
        
        self.E_In[self.t] = E_In
        self.trans = T
        self.evap = E
        self.net_rain_cur = net_rain_cur
    
    def _runoff_fun(self):
        """
        this module will calculate the runoff based on the initial soil moisture 
        and net precipitation
        
        Input:
            C:            Average soil moisture
            Pn:           Precipitation after interception loss
            runoff_par:   runoff parameters ['Cm','B']
            
        Output:
            runoff_cur:     Runoff at current time step
        """
        #Cm = self.runoff_par['Cm']
        #B = self.runoff_par['B']
        #F = 1 - (1- self.sm[:,self.t].mean()/Cm)**B 
        #self.runoff_cur = self.net_rain_cur*F
        #self.runoff[self.t] = self.runoff_cur
        
        # chen and dudhia
        Kdt_ref = 3.0
        Kref = 2e-6
        theta_s = self.soil_par['f']*np.exp(-self.mid_z/self.soil_par['fl'])
        Dx = theta_s - self.sm[:,self.t]
        Dx = Dx*self.mid_z
        Dx = Dx[:3].sum()
        Kdt = Kdt_ref*self.soil_par['Ks']/Kref
        
        Pn = self.net_rain_cur
        Imax = Pn*(Dx*(1-np.exp(-Kdt)))/(Pn+Dx*(1-np.exp(-Kdt)))
        
        self.runoff_cur = Pn - Imax 
        self.runoff[self.t] = self.runoff_cur
        
        
        
    def _soil_fun(self):
        """
        Input:
            soil_par     : soil hydraulic parameters
            z            : thicknes of layers
            R            : runoff
            no_layer     : no. of layers
            theta_0      : initial soil moisture
            root_frac    : root fraction in each layer
            T            : transpiration
            Pn           : net precipitation (precipitation - interception)
            E            : soil evaporation
            Pu           : pumping
            dt           : time step
        Output:
            theta_1: soil moisture for next time step
            Re: recharge (L)
        """
        # convert the fluxes from L to L/T
        self.runoff_cur /= self.dt
        self.evap /= self.dt
        self.trans /= self.dt
        self.net_rain_cur /= self.dt
        self.pumping_cur /= self.dt
        
        # initialize soil moisture at next time step        
        theta_1_mat = np.zeros(self.no_layer)
                
        # estimate hydraulic properties
        K = np.zeros((self.no_layer,1))
        D = np.zeros((self.no_layer,1))
        for i in range(self.no_layer):
            if i<self.no_layer-1:
                # using the maximum value of theta
                #K[i], D[i] = self._shp(max(self.sm[i,self.t],self.sm[i+1, self.t]),i)
                # using the arithmatic mean of theta
                K[i], D[i] = self._shp(0.5*(self.sm[i, self.t]+self.sm[i+1, self.t]),i)
            else:
                K[i], D[i] = self._shp(self.sm[i,self.t],i)
        K = K.flatten()*np.exp(-self.mid_z/self.soil_par['zl'])
        D = D.flatten()*np.exp(-self.mid_z/self.soil_par['zl'])
        
        # calculate stress in soil moisture and subsequently the actual 
        # evaporation and transpiration
        self._smi_fun()
        AE = self.evap*self.SSMI
        self._transpiration_fun()
        AT = self.AT 
                
        # set up the A and U matrix
        A = np.zeros((self.no_layer, self.no_layer))
        U = np.zeros((self.no_layer,1))
        z = self.z
        for i in range(self.no_layer):
            if i == 0:
                A[0,0] = -D[1]/(0.5*z[1]*(z[1]+z[2]))
                A[0,1] = D[1]/(0.5*z[1]*(z[1]+z[2]))
                U[0] = (-AT[0] - K[0] + self.net_rain_cur - AE - self.runoff_cur \
                + self.pumping_cur)/z[0]
            elif i == self.no_layer-1:
                A[i,i] = -D[i-1]/(0.5*z[i]*(z[i-1]+z[i]))
                A[i,i-1] = D[i-1]/(0.5*z[i]*(z[i-1]+z[i])) 
                U[i] = (-AT[i] + K[i-1] - K[i])/z[i]
            else:
                A[i,i-1] = D[i-1]/(0.5*z[i]*(z[i-1]+z[i]))
                A[i,i+1] = D[i]/(0.5*z[i]*(z[i]+z[i+1]))
                A[i,i] = -A[i,i-1] -A[i,i+1]
                U[i] = (-AT[i] +K[i-1] - K[i])/z[i]
                    
            # convert from A,U to F,G
            F = np.eye(self.no_layer) + A*self.dt
            #    if (F>1.4).any() | (F<0.6).any():
            #        F = expm(A*dt)
            G = np.dot(F,U)*self.dt
            
            # calculate theta for next time step
            theta_1 = np.dot(F, self.sm[:,self.t]) + G.flatten()
            
            # convert recharge from L/T to L
            Re = K[-1]*self.dt
            
            # remove the water as hortonian runoff, 
            # if the soil moisture exceeds saturation
            if theta_1[0] >= self.soil_par['f']:
                HR = (theta_1[0]-self.soil_par['f'])*z[0]
                theta_1[0] = self.soil_par['f']
            else:
                HR = 0

            #check for the range of the theta
            theta_s = self.soil_par['f']*np.exp(-self.mid_z/self.soil_par['fl'])
            wp = self.ET_par['trans_wp']*np.exp(-self.mid_z/self.soil_par['fl'])
            for j in range(self.no_layer):
                if theta_1[j]>theta_s[j]:
                    theta_1[j] = theta_s[j]
                if theta_1[j]<wp[j]:
                    theta_1[j] = wp[j]
            
            # put the result of this pixel into matrix
            self.sm[:,self.t+1] = theta_1.flatten()
            self.G = G
            self.F = F
            self.theta_1 = theta_1
            self.recharge[self.t] = Re
            self.actual_evap[self.t] = AE*self.dt
            self.actual_trans[self.t] = AT.sum()*self.dt
            self.horton_runoff[self.t] = HR
            
    def _smi_fun(self):
        """
        this module computes the surface soil moisture stress index, and root zone soil moisture 
        stress index
        """
        
        # calculate surface soil moisture index
        SSMI = (self.sm[0,self.t] - self.soil_par['evap_wp'])/(
                self.soil_par['evap_fc'] - self.soil_par['evap_wp'])
                
        if SSMI > 1: 
            SSMI = 1
        elif SSMI<0:
            SSMI = 0
    
        # calculate root zone soil moisture index
        RZSMI = np.zeros((self.no_layer,))
        
        for i in range(self.no_layer):
            trans_wp = self.ET_par['trans_wp'][i]
            trans_fc = self.ET_par['trans_fc'][i]
            if (self.sm[i,self.t] < trans_wp):
                RZSMI[i] = 0
            elif self.sm[i,self.t] > trans_fc:
                RZSMI[i] = 1
            else:
                
                RZSMI[i] = (self.sm[i,self.t]-trans_wp)/(trans_fc - trans_wp)
            
        
        self.SSMI = SSMI
        self.RZSMI = RZSMI
    
    
    def _transpiration_fun(self):
        """
        this function computes the actual transpiration for all the soil layers
        """
        # root distribution
        Lrd = self.Lrd
        Rd = self.Rd[self.t]
        r_density = np.empty(self.no_layer)
        for i in range(self.no_layer):
            if i==0:
                z1 = 0
            else:
                z1 = np.sum(self.z[:i])
            z2 = np.sum(self.z[:i+1])
            if z2>Rd:
                z2 = Rd
            if z1>z2:
                z1 = z2
            
            r_density[i] = np.exp(-z1/Lrd) - np.exp(-z2/Lrd)
        r_density = r_density/( 1 - np.exp(-Rd/Lrd) )
        
        self.r_density = r_density
        self.AT = self.RZSMI*r_density*self.trans
    

    def _shp(self, theta,i):
        """
        soil hydraulic properties module
        i is the layer
        """
        
        qr = self.soil_par['qr']*np.exp(-self.mid_z[i]/self.soil_par['fl'])
        f = self.soil_par['f']*np.exp(-self.mid_z[i]/self.soil_par['fl'])
        a = self.soil_par['a']
        n = self.soil_par['n']
        Ks = self.soil_par['Ks']
        l = self.soil_par['l']
        
        m = 1-1/n
        Se = (theta-qr)/(f - qr)
        if Se>=0.99:
            Se = 0.99
        elif Se<=0.01:
            Se = 0.01
        K = Ks*Se**l*(1-(1-Se**(1/m))**m)**2
        D = K/(a*(f-qr)*m*n*(Se**(1/m+1))*(Se**(-1/m)-1)**m)
        return K, D
    
    def _surface_storage_fun(self):
        """
        this module stores the surface water
        and give as recharge to the groundwater model
        """
        # update the storage based on the surface and hortonian runoff
        surface_storage = self.surface_storage[self.t] \
                                            + self.runoff_cur \
                                            + self.horton_runoff[self.t]
        a = self.surface_storage_par['a']
        b = self.surface_storage_par['b']
        Rep = a*surface_storage**b
        
        self.surface_storage[self.t+1] = surface_storage - Rep
        self.Rep = Rep                
        

    def _gw_fun(self):
        """
        Groundwater module
        """
        F = self.gw_par['F']
        G = self.gw_par['G']
        hmin = self.gw_par['hmin']
        
        self.sy = F/G
        self.lam = (1-F)*self.sy
        
        # net input = recharge - discharge
        u = self.recharge[self.t]-self.pumping_cur + self.Rep
        self.gw_level[self.t+1] = F*(self.gw_level[self.t]-hmin) + G*u + hmin
        
        dzn = self.gw_level[self.t+1] - self.gw_level[self.t] 
        self.discharge = u - self.sy*(dzn) # simulated discharge
        self.z[-1] = self.z[-1] - dzn
        #if self.t<30:
        #    print self.recharge[self.t]
        #    print self.z[-1]
                                   
        
        
    def _write_output(self):
        """
        This will write the data in the xls format
        
        """
        # open the xls workbook
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet('variables')
        # write the header
        sheet.write(0,0,'year')
        sheet.write(0,1,'doy')
        sheet.write(0,2,'gw level')
        for i in range(self.no_layer):
            sheet.write(0,3+i,'SM - %i'%(i+1))
        # write the data    
        for i in range(self.max_t):
            sheet.write(i+1,0,self.year[i])
            sheet.write(i+1,1,self.doy[i])
            sheet.write(i+1,2,self.gw_level[i])
            for j in range(self.no_layer):
                sheet.write(i+1,3+j,self.sm[j,i])
        
        sheet = wbk.add_sheet('flux')
        # write the header
        sheet.write(0,0,'year')
        sheet.write(0,1,'doy')
        sheet.write(0,2,'rain')
        sheet.write(0,3,'PET')
        sheet.write(0,4,'lai')
        sheet.write(0,5,'pumping')
        sheet.write(0,6,'actual evap')
        sheet.write(0,7,'actual trans')
        sheet.write(0,8,'E_In')
        sheet.write(0,9,'AET')
        sheet.write(0,10,'recharge')
        sheet.write(0,11,'runoff')
        
        # write the data    
        for i in range(self.max_t):
            sheet.write(i+1,0,self.year[i])
            sheet.write(i+1,1,self.doy[i])
            sheet.write(i+1,2,self.rain[i])
            sheet.write(i+1,3,self.pet[i])
            sheet.write(i+1,4,self.lai[i])
            sheet.write(i+1,5,self.pumping[i])
            sheet.write(i+1,6,self.actual_evap[i])
            sheet.write(i+1,7,self.actual_trans[i])
            sheet.write(i+1,8,self.E_In[i])
            sheet.write(i+1,9,self.actual_evap[i]+self.actual_trans[i]+self.E_In[i])
            sheet.write(i+1,10,self.recharge[i])
            sheet.write(i+1,11,self.runoff[i])
            
        wbk.save(self.ofile_name)
        
        output_message = 'Output data writting completed sucessfully'
        self._colored_output(output_message, 32)
        

class CSGLM_ENKF(CSGLM):
    """
    This is the main class of the Ensemble Kalman Filter (EnKF)
    coupled with the CSGLM model. The model is given in the class CSGLM.
        
    This will read the input data,
    do the processing
    and then write the output files
    
    """
    
    def __init__(self,input_file):
        """
        Input:
            input_file: the file which contains all the information
            including forcing and parameters.
        """      
        self.input_file = input_file
        self.n_ens = 10
        # read the input data
        self._read_input()
        
        # initialize the variables and output file
        self.initialize()
        
        ################ run the model ########################
        for t in range(self.max_t):
            self.t = t
              
            # get forcing data at current time step        
            self._get_forcing()
            
            # perturb the soil par ensemble
            self._perturb_soil_par_ens()
                        
            # call the unsat module with ensemble
            for ens in range(self.n_ens):
                self.ens = ens
                
                # call the interception module
                self._interception_ens_fun()
                
                # call the runoff module
                self._runoff_ens_fun()
                
                # call the soil module
                self._soil_ens_fun()
                
                # call the surface storage module
                self._surface_storage_ens_fun()
                
                # call the goundwater module
                self._gw_ens_fun()
        
                
            # ensemble kalmfan filter
            self._enkf_par()

            self._enkf_ET()
            
            self._write_output()                
                
                
        self.nc_file.close() # close the output file


    def initialize(self):
        """
        this initializes all the required variables
        and open the netcdf file for writting
        also generates the initial ensemble of the soil hydraulic parameters
        """
        max_t = int(self.final_time/self.dt)
        self.max_t = max_t                       
        
        #initialize variables
        self.surface_storage_ens = np.zeros((self.n_ens, self.max_t+1))   
        self.gw_level_ens = np.zeros((self.n_ens, self.max_t+1))
        
        self.gw_level_ens[:,0] = self.initial_gwl
        self.sm_ens = self.initial_sm + 0.02*np.random.normal(size=(self.n_ens,self.no_layer))
        
        # open file for writing
        file = nc.NetCDFFile(self.ofile_name, 'w')
        setattr(file, 'title', 'output of the model ambhas.csglm_enkf')
        now = datetime.datetime.now()
        setattr(file, 'description', 'The model was run at %s'%(now.ctime()))
        file.createDimension('depth', self.no_layer)
        file.createDimension('time', self.max_t+1)
        file.createDimension('ensemble', self.n_ens)
        
        # depth
        varDims = 'depth',
        depth = file.createVariable('depth', 'd', varDims)
        depth.units = 'm'
        depth[:] = self.z
        
        # time (year and doy)
        varDims = 'time',
        self.nc_year = file.createVariable('year', 'd', varDims)
        self.nc_doy = file.createVariable('doy', 'd', varDims)
        
        # soil moisture
        varDims = 'ensemble', 'depth', 'time'
        self.nc_sm = file.createVariable('sm','d', varDims)
        self.nc_sm.units = 'v/v'
        self.nc_sm[:,:,0] = self.sm_ens
        
        # recharge, aet 
        varDims = 'time',
        self.nc_aet = file.createVariable('aet','d',varDims)
        self.nc_aet.units = 'mm'
        self.nc_recharge = file.createVariable('recharge','d',varDims)
        self.nc_recharge.units = 'mm'
        
        # gw level
        varDims = 'ensemble', 'time'
        self.nc_gw_level_ens = file.createVariable('gw_level_ens','d',varDims)
        self.nc_gw_level_ens.units = 'm'
        self.nc_gw_level_ens[:,0] = self.gw_level_ens[:,0]
        
        # soil hydraulic parameters
        varDims = 'ensemble','time'
        self.nc_qr = file.createVariable('qr','d',varDims)
        self.nc_qr.units = 'v/v'
        self.nc_f = file.createVariable('f','d',varDims)
        self.nc_f.units = 'v/v'    
        self.nc_a = file.createVariable('a','d',varDims)
        self.nc_a.units = '1/m'
        self.nc_n = file.createVariable('n','d',varDims)
        self.nc_n.units = '-' 
        self.nc_Ks = file.createVariable('Ks','d',varDims)
        self.nc_Ks.units = 'm/s'
        self.nc_l = file.createVariable('l','d',varDims)
        self.nc_l.units = '-' 
        
        self.nc_file = file
        
        # generate soil hydraulic parameters
        self._generate_soil_par_ens()
        
        

    def _generate_soil_par_ens(self):
        """
        this uses the LHS to generate the ensemble of the parameters
        
        this also computes the perturbation needed to perturb the parameters
        which is done in another function
        """
               
        #gaussian perturbation
        v = np.random.normal(size=(self.n_ens,6))
        v = v-np.tile(v.mean(axis=0),(self.n_ens,1))
        qr = self.shp_ens['qr']  + v[:,0]*self.shp_ens['qr']*0.1
        f = self.shp_ens['f']  + v[:,1]*self.shp_ens['f']*0.1
        a = self.shp_ens['a']    + v[:,2]*self.shp_ens['a']*0.1
        n = self.shp_ens['n']            + v[:,3]*self.shp_ens['n']*0.1
        Ks = self.shp_ens['Ks']          + v[:,4]*self.shp_ens['Ks']*0.1
        l = self.shp_ens['l']            + v[:,5]*self.shp_ens['l']*0.1

        # check for the range of generated parameters
        qr[qr>self.qr_max] = self.qr_max
        f[f>self.f_max] = self.f_max
        a[a>self.a_max] = self.a_max
        n[n>self.n_max] = self.n_max
        Ks[Ks>self.Ks_max] = self.Ks_max
        l[l>self.l_max] = self.l_max
        
        qr[qr<self.qr_min]  = self.qr_min
        f[f<self.f_min]  = self.f_min
        a[a<self.a_min]     = self.a_min
        n[n<self.n_min]                 = self.n_min
        Ks[Ks<self.Ks_min]              = self.Ks_min
        l[l<self.l_min]                 = self.l_min
        
        soil_par_ens = {}
        soil_par_ens['qr'] = qr
        soil_par_ens['f'] = f
        soil_par_ens['a'] = a
        soil_par_ens['n'] = n
        soil_par_ens['Ks'] = Ks
        soil_par_ens['l'] = l
        
        self.soil_par_ens = soil_par_ens
        
        #perturbation parameter
        soil_pert = {}
        soil_pert['qr'] = (self.qr_max - self.qr_min)*0.1/100.0
        soil_pert['f'] = (self.f_max - self.f_min)*0.1/100.0
        soil_pert['a'] =  (self.a_max - self.a_min)*0.1/100.0
        soil_pert['n'] =      (self.n_max - self.n_min)*0.1/100.0
        soil_pert['Ks'] =     (self.Ks_max - self.Ks_min)*0.1/100.0
        soil_pert['l'] =      (self.l_max - self.l_min)*0.1/100.0
        
        self.soil_pert = soil_pert

    def _read_input(self):
        """
        This checks if all the required input sheets are present in the xls file,
        read the data from input file, which can be used later in other functions
        """
    
        # list of required files in the input directory
        input_sheets = ['ind', 'forcing', 'initial_condition', 'gw_par',
                       'runoff_par', 'units', 'root_info', 'temporal_info',
                       'spatial_info', 'ET_par', 'soil_hyd_par', 'output_par']
        
        # check if all the required sheets are present or not
        self._check_sheets(input_sheets, self.input_file)
        
        # read the legend
        self._read_ind()
        
        # read the spatial data
        self._read_spatial()
        
        # read the temporal data
        self._read_temporal()

        # read the root distribution data
        self._read_root_distribution()
        
        # read the units 
        self._read_units()
        
        # read the initial condition
        self._read_initial_condition()
        
        # read the soil hydraulic properties data
        self._read_shp_ens()
        
        # read the parameters related to runoff
        self._read_runoff_par()
        
        # read the parameters related to surface storage
        self._surface_storage_par()
        
        # read the groundwaer parameters data
        self._read_gw_par()
        
        # read the ET parameter data
        self._read_ET_par()
        
        # read the forcing infomation
        self._read_forcing()
        
        # read the outfile name
        self._read_ofile_name()
        
        # print the reading status
        output_message = 'Input data reading completed sucessfully'
        self._colored_output(output_message, 32)

    def _read_initial_condition(self):
        """
        read initial condition
        """
        #get the row number from the ind
        j = self.ind['initial_condition']
        
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('initial_condition')
        theta_0 = sheet.row_values(j,2)
        self.initial_gwl = sheet.cell_value(j,1)
        self.initial_sm = np.array(theta_0)
        
               

    def _read_shp_ens(self):
        """
        read the soil hydraulic parameters
        """
        #get the row number from the ind
        j = self.ind['soil_hyd_par']
        
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('soil_hyd_par')
        shp_ens = {}
        shp_ens['qr'] = sheet.cell_value(j,1)
        shp_ens['f'] = sheet.cell_value(j,2)
        shp_ens['a'] = sheet.cell_value(j,3)
        shp_ens['n'] = sheet.cell_value(j,4)
        shp_ens['Ks'] = sheet.cell_value(j,5)
        shp_ens['l'] = sheet.cell_value(j,6)
        #soil_par['evap_wp'] = sheet.cell_value(j,7)
        #soil_par['evap_fc'] = sheet.cell_value(j,8)
        shp_ens['zl'] = sheet.cell_value(j,9)
        shp_ens['fl'] = sheet.cell_value(j,10)
        
        m = 1-1/shp_ens['n']
        # evaluate wilting point and field capacity
        shp_ens['evap_fc'] = self.psi2theta(-0.33, shp_ens['qr'], shp_ens['f'], 
                               shp_ens['a'], m, shp_ens['n'])
        
        shp_ens['evap_wp'] = self.psi2theta(-15, shp_ens['qr'], shp_ens['f'], 
                               shp_ens['a'], m, shp_ens['n'])
                               
        self.shp_ens = shp_ens
        
        # maximum and minimum range of the paramters
        self.qr_min, self.qr_max = 0.02, 0.12 
        self.f_min, self.f_max = 0.25, 0.4 
        self.a_min, self.a_max = 2, 5 
        self.n_min, self.n_max = 1.4, 2.4 
        self.Ks_min, self.Ks_max = 1e-6, 1e-5 
        self.l_min, self.l_max = 0.4, 0.6 


    def _perturb_soil_par_ens(self):
        """
        this functions perturb the soil hydraulic parameters 
        using the gaussian random variables
        """
        v = np.random.normal(size=(self.n_ens,6))
        v = v-np.tile(v.mean(axis=0),(self.n_ens,1))
        qr = self.soil_par_ens['qr']+self.soil_pert['qr']*v[:,0]
        f = self.soil_par_ens['f']+self.soil_pert['f']*v[:,1]
        a = self.soil_par_ens['a']+self.soil_pert['a']*v[:,2]
        n = self.soil_par_ens['n']+self.soil_pert['n']*v[:,3]
        Ks = self.soil_par_ens['Ks']+self.soil_pert['Ks']*(v[:,4]-v[:,4].mean())
        l = self.soil_par_ens['l']+self.soil_pert['l']*v[:,5]
        

        # check for the range of generated parameters
        qr[qr>self.qr_max] = self.qr_max
        f[f>self.f_max] = self.f_max
        a[a>self.a_max] = self.a_max
        n[n>self.n_max] = self.n_max
        Ks[Ks>self.Ks_max] = self.Ks_max
        l[l>self.l_max] = self.l_max
        
        qr[qr<self.qr_min]  = self.qr_min
        f[f<self.f_min]  = self.f_min
        a[a<self.a_min]     = self.a_min
        n[n<self.n_min]                 = self.n_min
        Ks[Ks<self.Ks_min]              = self.Ks_min
        l[l<self.l_min]                 = self.l_min        

        soil_par_ens = {}
        soil_par_ens['qr'] = qr
        soil_par_ens['f'] = f
        soil_par_ens['a'] = a
        soil_par_ens['n'] = n
        soil_par_ens['Ks'] = Ks
        soil_par_ens['l'] = l        
        m = 1-1/n
        soil_par_ens['evap_fc'] = self.psi2theta(-0.33, qr, f, a, m, n)
        
        soil_par_ens['evap_wp'] = self.psi2theta(-15, qr, f, a, m, n)
        self.soil_par_ens = soil_par_ens
        
        fl = self.shp_ens['fl']
        mid_z = self.mid_z
        ET_par = {}
        ET_par['trans_fc'] = self.psi2theta(-0.33, qr, f, a, m, n)
        ET_par['trans_wp'] = self.psi2theta(-15, qr, f, a, m, n)
        
        self.ET_par = ET_par

    def _runoff_ens_fun(self):
        """
        this module will calculate the runoff based on the initial soil moisture 
        and net precipitation
        
        Input:
            C:            Average soil moisture
            Pn:           Precipitation after interception loss
            runoff_par:   runoff parameters ['Cm','B']
            
        Output:
            runoff_cur:     Runoff at current time step
        """
        #Cm = self.runoff_par['Cm']
        #B = self.runoff_par['B']
        #F = 1 - (1- self.sm[:,self.t].mean()/Cm)**B 
        #self.runoff_cur = self.net_rain_cur*F
        #self.runoff[self.t] = self.runoff_cur
        ens = self.ens
        # chen and dudhia
        Kdt_ref = 3.0
        Kref = 2e-6
        theta_s = self.soil_par_ens['f'][ens]*np.exp(-self.mid_z/self.shp_ens['fl'])
        
        Dx = theta_s - self.sm_ens[ens]
        Dx = Dx*self.mid_z
        Dx = Dx[:3].sum()
        Kdt = Kdt_ref*self.soil_par_ens['Ks'][ens]/Kref
        
        Pn = self.net_rain_cur
        Imax = Pn*(Dx*(1-np.exp(-Kdt)))/(Pn+Dx*(1-np.exp(-Kdt)))
        
        self.runoff_cur = Pn - Imax 
        self.runoff = 1.0*self.runoff_cur

    def _interception_ens_fun(self):
        """
        Input:
            lai_cur:    LAI at the current time step
            pet_cur:     PET at the current time step
            rain_cur:    Rainfall at the current time step
            
        Output:
            E_In:     Evaporation from Interception
            T:        Transpiration
            E:        Evaporation
            net_rain_cur:   Net rainfall (precipitation-interception loss) at 
            current time step
        """
        In = self.lai[self.t]*0.2/1000.0
        soil_cover = np.exp(-0.5*self.lai_cur)
        veg_cover = 1 - soil_cover
        
        E_In = np.min([veg_cover*self.rain_cur, veg_cover*self.pet_cur, veg_cover*In])
        T = np.min([veg_cover*self.pet_cur - 0.2*E_In, 1.2*self.pet_cur - E_In])
        E = np.min([soil_cover*self.pet_cur, 1.2*self.pet_cur-T-E_In])
        net_rain_cur = self.rain_cur - E_In
        
        
        self.E_In = E_In
        self.trans = T
        self.evap = E
        self.net_rain_cur = net_rain_cur

    def _soil_ens_fun(self):
        """
        Input:
            soil_par     : soil hydraulic parameters
            z            : thicknes of layers
            R            : runoff
            no_layer     : no. of layers
            theta_0      : initial soil moisture
            root_frac    : root fraction in each layer
            T            : transpiration
            Pn           : net precipitation (precipitation - interception)
            E            : soil evaporation
            Pu           : pumping
            dt           : time step
        Output:
            theta_1: soil moisture for next time step
            Re: recharge (L)
        """
        # convert the fluxes from L to L/T
        self.runoff_cur /= self.dt
        self.evap /= self.dt
        self.trans /= self.dt
        self.net_rain_cur /= self.dt
        self.pumping_cur /= self.dt
        
        # initialize soil moisture at next time step        
        theta_1_mat = np.zeros(self.no_layer)

        # get the information about current ensemble
        ens = self.ens
        sm = self.sm_ens[ens]
        
        # estimate hydraulic properties
        K = np.zeros((self.no_layer,1))
        D = np.zeros((self.no_layer,1))
        for i in range(self.no_layer):
            if i<self.no_layer-1:
                # using the maximum value of theta
                #K[i], D[i] = self._shp(max(self.sm[i,self.t],self.sm[i+1, self.t]),i)
                # using the arithmatic mean of theta
                K[i], D[i] = self._shp(0.5*(sm[i]+sm[i+1]),i)
            else:
                K[i], D[i] = self._shp(sm[i],i)
        K = K.flatten()*np.exp(-self.mid_z/self.shp_ens['zl'])
        D = D.flatten()*np.exp(-self.mid_z/self.shp_ens['zl'])
        
        # calculate stress in soil moisture and subsequently the actual 
        # evaporation and transpiration
        self._smi_fun()
        AE = self.evap*self.SSMI
        self._transpiration_fun()
        AT = self.AT 
                
        # set up the A and U matrix
        A = np.zeros((self.no_layer, self.no_layer))
        U = np.zeros((self.no_layer,1))
        z = self.z
        for i in range(self.no_layer):
            if i == 0:
                A[0,0] = -D[1]/(0.5*z[1]*(z[1]+z[2]))
                A[0,1] = D[1]/(0.5*z[1]*(z[1]+z[2]))
                U[0] = (-AT[0] - K[0] + self.net_rain_cur - AE - self.runoff_cur \
                + self.pumping_cur)/z[0]
            elif i == self.no_layer-1:
                A[i,i] = -D[i-1]/(0.5*z[i]*(z[i-1]+z[i]))
                A[i,i-1] = D[i-1]/(0.5*z[i]*(z[i-1]+z[i])) 
                U[i] = (-AT[i] + K[i-1] - K[i])/z[i]
            else:
                A[i,i-1] = D[i-1]/(0.5*z[i]*(z[i-1]+z[i]))
                A[i,i+1] = D[i]/(0.5*z[i]*(z[i]+z[i+1]))
                A[i,i] = -A[i,i-1] -A[i,i+1]
                U[i] = (-AT[i] +K[i-1] - K[i])/z[i]
                    
            # convert from A,U to F,G
            F = np.eye(self.no_layer) + A*self.dt
            #    if (F>1.4).any() | (F<0.6).any():
            #        F = expm(A*dt)
            G = np.dot(F,U)*self.dt
            
            # calculate theta for next time step
            theta_1 = np.dot(F, sm) + G.flatten()
            
            # convert recharge from L/T to L
            Re = K[-1]*self.dt
            
            # remove the water as hortonian runoff, 
            # if the soil moisture exceeds saturation
            if theta_1[0] >= self.soil_par_ens['f'][ens]:
                HR = (theta_1[0]-self.soil_par_ens['f'][ens])*z[0]
                theta_1[0] = self.soil_par_ens['f'][ens]
            else:
                HR = 0

            #check for the range of the theta
            theta_s = self.soil_par_ens['f'][ens]*np.exp(-self.mid_z/self.shp_ens['fl'])
            wp = self.ET_par['trans_wp'][ens]*np.exp(-self.mid_z/self.shp_ens['fl'])
            for j in range(self.no_layer):
                if theta_1[j]>theta_s[j]:
                    theta_1[j] = theta_s[j]
                if theta_1[j]<wp[j]:
                    theta_1[j] = wp[j]
            
            # put the result of this pixel into matrix
            self.sm_ens[ens] = theta_1.flatten()
            self.G = G
            self.F = F
            self.theta_1 = theta_1
            self.recharge = Re
            self.actual_evap = AE*self.dt
            self.actual_trans = AT.sum()*self.dt
            self.horton_runoff = HR

    def _smi_fun(self):
        """
        this module computes the surface soil moisture stress index, and root zone soil moisture 
        stress index
        """
        ens = self.ens
        sm = self.sm_ens[ens]
        # calculate surface soil moisture index
        SSMI = (sm[0] - self.soil_par_ens['evap_wp'][ens])/(
                self.soil_par_ens['evap_fc'][ens] - self.soil_par_ens['evap_wp'][ens])
                
        if SSMI > 1: 
            SSMI = 1
        elif SSMI<0:
            SSMI = 0
    
        # calculate root zone soil moisture index
        RZSMI = np.zeros((self.no_layer,))
        mid_z = self.mid_z
        fl = self.shp_ens['fl']
        
        for i in range(self.no_layer):
            trans_wp = self.ET_par['trans_wp'][ens]*np.exp(-mid_z/fl)[i]
            trans_fc = self.ET_par['trans_fc'][ens]*np.exp(-mid_z/fl)[i]
            if (sm[i] < trans_wp):
                RZSMI[i] = 0
            elif sm[i] > trans_fc:
                RZSMI[i] = 1
            else:
                
                RZSMI[i] = (sm[i]-trans_wp)/(trans_fc - trans_wp)
            
        
        self.SSMI = SSMI
        self.RZSMI = RZSMI

    def _surface_storage_ens_fun(self):
        """
        this module stores the surface water
        and give as recharge to the groundwater model
        """
        ens = self.ens
        # update the storage based on the surface and hortonian runoff
        surface_storage = self.surface_storage_ens[ens,self.t] \
                                            + self.runoff_cur \
                                            + self.horton_runoff
        a = 1.0*self.surface_storage_par['a']
        b = 1.0*self.surface_storage_par['b']
        Rep = a*surface_storage**b
        #print type(surface_storage)
        
        self.surface_storage_ens[ens,self.t+1] = surface_storage - Rep
        self.Rep = Rep     

    def _gw_ens_fun(self):
        """
        Groundwater module
        """
        ens = self.ens
        F = self.gw_par['F']
        G = self.gw_par['G']
        hmin = self.gw_par['hmin']
        
        self.sy = F/G
        self.lam = (1-F)*self.sy
        
        # net input = recharge - discharge
        u = self.recharge-self.pumping_cur + self.Rep
        self.gw_level_ens[ens,self.t+1] = F*(self.gw_level_ens[ens,self.t]-hmin) + G*u + hmin
        
        dzn = self.gw_level_ens[ens,self.t+1] - self.gw_level_ens[ens,self.t] 
        self.discharge = u - self.sy*(dzn) # simulated discharge
        self.z_ens[ens,-1] = self.z_ens[ens,-1] - dzn
        
    def _read_spatial(self):
        """
        Read the spatial info
        """
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('spatial_info')
        # get the row number from the ind
        j = self.ind['spatial_info']
        no_layer = int(sheet.cell_value(j,1))
        z = sheet.row_values(j,2)
        if no_layer != len(z):
            raise ValueError('The length of the thickness_layers\
            should be equal to the No_layer')
        
        self.no_layer = no_layer
        self.z = z
        self.z_ens = np.tile(z,(self.n_ens,1))
        
        #mid depth of the layers
        depth = np.zeros(no_layer+1)
        depth[1:] = np.cumsum(z)
        self.mid_z = 0.5*(depth[1:]+depth[:-1])
    
    def _enkf_par(self):
        """
        ensemble kalman filter
        """
        # make the state vector which contains the soil moisture at different 
        #depths and soil parameters
        x = self.sm_ens + 0.005*np.random.normal(size=self.no_layer)
        qr = self.soil_par_ens['qr']
        f = self.soil_par_ens['f']
        a = self.soil_par_ens['a']
        n = self.soil_par_ens['n']
        Ks = self.soil_par_ens['Ks']
        l = self.soil_par_ens['l']
        soil_par = (np.vstack([qr, f, a, n, Ks, l])).T
        X = np.hstack([x, soil_par])
        
        # compute the covariance matrix of the state+par
        X_bar = np.tile(X.mean(axis=0),(10,1))
        X_X_bar = X-X_bar
        cov_XX = np.dot(X_X_bar.T,X_X_bar) + 1e-6*np.eye(self.no_layer+6)
        cov_XX = 0.5*(cov_XX + cov_XX.T)
        
        # get the measurement of the ssm at the current time
        # and generate its ensemble and compute its covariance matrix
        e = np.zeros((self.n_ens, self.no_layer+6))
        if np.isnan(self.meas_sm_mean[self.t-1]):
            e[:,0] = 0
            v = 0.01*np.random.normal(size=(self.n_ens,self.no_layer+6))
        else:
            e[:,0] = self.meas_sm_mean[self.t-1] - self.sm_ens[:,0].mean()
            v = self.meas_sm_std[self.t-1]*np.random.normal(size=(self.n_ens,self.no_layer+6))
            
        v = v-np.tile(v.mean(axis=0),(self.n_ens,1))
        ev = e + v
        cov_ee = np.dot(ev.T, ev) + 1e-6*np.eye(self.no_layer+6)
        cov_ee = 0.5*(cov_ee + cov_ee.T)
        
        # compute kalaman gain
        K = np.dot(cov_XX, np.linalg.pinv(cov_XX+cov_ee))
        
        # update the measurment
        v = np.random.normal(size=(self.n_ens,))
        v = v-v.mean()
        e[:,0] = e[:,0]+0.005*v
        K = 0.5*(K + K.T)
        usm_par = X + np.dot(K,e.T).T      
        temp = np.dot(K,e.T).T     
        
        self.usm_par = usm_par
        #if self.t<=5:
        #    print self.t, usm_par[:,self.no_layer+4]/soil_par[:,4]
        # check for the range of the updated ensemble
        # soil moisture
        sm_ens = usm_par[:,:self.no_layer]
        sm_ens[sm_ens<0] = 0
        sm_ens[sm_ens>1] = 1
        v = 0.001*np.random.normal(size=(sm_ens.shape))
        v = v-np.tile(v.mean(axis=0),(self.n_ens,1))
        self.sm_ens = sm_ens + v
        # soil parameters
        qr = usm_par[:,self.no_layer+0]
        f = usm_par[:,self.no_layer+1]
        a = usm_par[:,self.no_layer+2]
        n = usm_par[:,self.no_layer+3]
        Ks = usm_par[:,self.no_layer+4]
        l = usm_par[:,self.no_layer+5]
        
        
        qr[qr>self.qr_max] = self.qr_max
        f[f>self.f_max] = self.f_max
        a[a>self.a_max] = self.a_max
        n[n>self.n_max] = self.n_max
        Ks[Ks>self.Ks_max] = self.Ks_max
        l[l>self.l_max] = self.l_max
        
        qr[qr<self.qr_min]  = self.qr_min
        f[f<self.f_min]  = self.f_min
        a[a<self.a_min]     = self.a_min
        n[n<self.n_min]                 = self.n_min
        Ks[Ks<self.Ks_min]              = self.Ks_min
        l[l<self.l_min]                 = self.l_min
        
        
        self.soil_par_ens['qr'] = qr
        self.soil_par_ens['f'] = f
        self.soil_par_ens['a'] = a
        self.soil_par_ens['n'] = n
        self.soil_par_ens['Ks'] = Ks
        self.soil_par_ens['l'] = l
        
        self.K = K
        self.cov_ee = cov_ee
        self.cov_XX = cov_XX
    
    def _enkf_ET(self):
        """
        ensemble kalman filter
        """
        # make the state vector which contains the soil moisture at different 
        #depths and soil parameters
        x = self.sm_ens + 0.005*np.random.normal(size=self.no_layer)
        qr = self.soil_par_ens['qr']
        f = self.soil_par_ens['f']
        a = self.soil_par_ens['a']
        n = self.soil_par_ens['n']
        Ks = self.soil_par_ens['Ks']
        l = self.soil_par_ens['l']
        soil_par = (np.vstack([qr, f, a, n, Ks, l])).T
        X = np.hstack([x, soil_par])
        
        # compute the covariance matrix of the state+par
        X_bar = np.tile(X.mean(axis=0),(10,1))
        X_X_bar = X-X_bar
        cov_XX = np.dot(X_X_bar.T,X_X_bar) + 1e-6*np.eye(self.no_layer+6)
        cov_XX = 0.5*(cov_XX + cov_XX.T)
        
        # get the measurement of the AET at the current time
        # and use it to generate ensemble of soil moisture
        err_aet = np.zeros(self.n_ens)
        for ens in range(self.n_ens):
            self.ens = ens
            self._smi_fun()
            AE = self.evap*self.SSMI
            self._transpiration_fun()
            AT = self.AT 
            
            err_aet[ens] = self.meas_aet[self.t] - AE - AT.sum() - self.E_In
        err_ae = err_aet.mean()*AE/(AE+AT.sum())
        err_at = err_aet.mean()*AT.sum()/(AE+AT.sum())
        
        e = np.zeros((self.n_ens, self.no_layer+6))
        e[:,0] = (err_ae + err_at*self.r_density[0])/self.z[0]
        e[:,1] = err_at*self.r_density[1]/self.z[1]
        e[:,2] = err_at*self.r_density[2]/self.z[2]
        e[:,3] = err_at*self.r_density[3]/self.z[3]
        e[:,4] = err_at*self.r_density[4]/self.z[4]
        v = 0.03*np.random.normal(size=(self.n_ens,self.no_layer+6))
            
        v = v-np.tile(v.mean(axis=0),(self.n_ens,1))
        ev = e + v
        cov_ee = np.dot(ev.T, ev) + 1e-6*np.eye(self.no_layer+6)
        cov_ee = 0.5*(cov_ee + cov_ee.T)
        
        #print cov_ee
        print self.t, e.max(), self.z[4]
        # compute kalaman gain
        K = np.dot(cov_XX, np.linalg.pinv(cov_XX+cov_ee))
        
        # update the measurment
        v = np.random.normal(size=(self.n_ens,))
        v = v-v.mean()
        e[:,0] = e[:,0]+0.005*v
        K = 0.5*(K + K.T)
        usm_par = X + np.dot(K,e.T).T      
        temp = np.dot(K,e.T).T     
        
        self.usm_par = usm_par
        #if self.t<=5:
        #    print self.t, usm_par[:,self.no_layer+4]/soil_par[:,4]
        # check for the range of the updated ensemble
        # soil moisture
        sm_ens = usm_par[:,:self.no_layer]
        sm_ens[sm_ens<0] = 0
        sm_ens[sm_ens>1] = 1
        v = 0.001*np.random.normal(size=(sm_ens.shape))
        v = v-np.tile(v.mean(axis=0),(self.n_ens,1))
        self.sm_ens = sm_ens + v
        # soil parameters
        qr = usm_par[:,self.no_layer+0]
        f = usm_par[:,self.no_layer+1]
        a = usm_par[:,self.no_layer+2]
        n = usm_par[:,self.no_layer+3]
        Ks = usm_par[:,self.no_layer+4]
        l = usm_par[:,self.no_layer+5]
        
        
        qr[qr>self.qr_max] = self.qr_max
        f[f>self.f_max] = self.f_max
        a[a>self.a_max] = self.a_max
        n[n>self.n_max] = self.n_max
        Ks[Ks>self.Ks_max] = self.Ks_max
        l[l>self.l_max] = self.l_max
        
        qr[qr<self.qr_min]  = self.qr_min
        f[f<self.f_min]  = self.f_min
        a[a<self.a_min]     = self.a_min
        n[n<self.n_min]                 = self.n_min
        Ks[Ks<self.Ks_min]              = self.Ks_min
        l[l<self.l_min]                 = self.l_min
        
        
        self.soil_par_ens['qr'] = qr
        self.soil_par_ens['f'] = f
        self.soil_par_ens['a'] = a
        self.soil_par_ens['n'] = n
        self.soil_par_ens['Ks'] = Ks
        self.soil_par_ens['l'] = l
        
        self.K = K
        self.cov_ee = cov_ee
        self.cov_XX = cov_XX

    def _read_forcing(self):
        """
        read the forcing data from xls file
        """
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('forcing')
        
        data_len = sheet.nrows-1
        year = np.zeros(data_len)
        doy = np.zeros(data_len)
        rain = np.zeros(data_len)
        pet = np.zeros(data_len)
        ndvi = np.zeros(data_len)
        pumping = np.zeros(data_len)
        meas_sm_mean = np.zeros(data_len)
        meas_sm_std = np.zeros(data_len)
        meas_aet = np.zeros(data_len)
    
        for i in xrange(data_len):
            year[i] = sheet.cell_value(i+1,0)
            doy[i] = sheet.cell_value(i+1,1)
            rain[i] = sheet.cell_value(i+1,2)
            pet[i] = sheet.cell_value(i+1,3)
            ndvi[i] = sheet.cell_value(i+1,4)
            pumping[i] = sheet.cell_value(i+1,5)
            meas_sm_mean[i] = sheet.cell_value(i+1,6)
            meas_sm_std[i] = sheet.cell_value(i+1,7)
            meas_aet[i] = sheet.cell_value(i+1,8)/1000.0
        
        self.year = year
        self.doy = doy
        self.meas_sm_mean = meas_sm_mean
        self.meas_sm_std = meas_sm_std
        self.meas_aet = meas_aet
        
        # if forcing data was in mm units, covert into m
        if self.forcing_units['rain'] == 'mm':
            self.rain = rain/1000.0
        elif self.forcing_units['rain'] == 'm':
            self.rain = rain
        else:
            raise ValueError("The units of rain should be either 'mm' or 'm' ")

        if self.forcing_units['pet'] == 'mm':
            self.pet = pet/1000.0
        elif self.forcing_units['pet'] == 'm':
            self.pet = pet
        else:
            raise ValueError("The units of PET should be either 'mm' or 'm' ")
            
        if self.forcing_units['pumping'] == 'mm':
            self.pumping = pumping/1000.0
        elif self.forcing_units['pumping'] == 'm':
            self.pumping = pumping
        else:
            raise ValueError("The units of pumping should be either 'mm' or 'm' ")
        
        # compute the fractional vegetation cover, rooting depth and lai
        ndvi_max = self.ndvi_max
        ndvi_min = self.ndvi_min
        ndvi[ndvi>ndvi_max] = ndvi_max
        ndvi[ndvi<ndvi_min] = ndvi_min
        
        fapar = 1.60*ndvi-0.02
        fapar_max = self.fapar_max
        
        lai_max = self.lai_max
        lai = lai_max*np.log(1-fapar)/np.log(1-fapar_max)
        
        Rd_max = self.Rd_max  
        Rd = Rd_max*lai/lai_max
        fc = ((ndvi-ndvi_max)/(ndvi_max-ndvi_min))**2
        
        self.kc = 0.8+0.4*(1-np.exp(-0.7*lai))
        self.ndvi = ndvi
        self.lai = lai        
        self.Rd = Rd
        self.fc = fc

    def _write_output(self):
        """
        this functions writes the output at each time step
        """
        # write the output
        self.nc_year[self.t] = (self.cur_year)
        self.nc_doy[self.t] = (self.cur_doy)
        self.nc_sm[:,:,self.t+1] = self.sm_ens
        self.nc_gw_level_ens[:,self.t+1] = self.gw_level_ens[:,self.t+1]
        #self.nc_recharge[self.t] = recharge_day
        #self.nc_aet[self.t] = aet_day
        self.nc_qr[:,self.t] = self.soil_par_ens['qr']
        self.nc_f[:,self.t] = self.soil_par_ens['f']
        self.nc_a[:,self.t] = self.soil_par_ens['a']
        self.nc_n[:,self.t] = self.soil_par_ens['n']
        self.nc_Ks[:,self.t] = self.soil_par_ens['Ks']
        self.nc_l[:,self.t] = self.soil_par_ens['l']
        #self.nc_recharge[:,self.t] = self.recharge
    
    def _shp(self, theta,i):
        """
        soil hydraulic properties module
        i is the layer
        """
        ens = self.ens
        qr = self.soil_par_ens['qr'][ens]*np.exp(-self.mid_z[i]/self.shp_ens['fl'])
        f = self.soil_par_ens['f'][ens]*np.exp(-self.mid_z[i]/self.shp_ens['fl'])
        a = self.soil_par_ens['a'][ens]
        n = self.soil_par_ens['n'][ens]
        Ks = self.soil_par_ens['Ks'][ens]
        l = self.soil_par_ens['l'][ens]
        
        m = 1-1/n
        Se = (theta-qr)/(f - qr)
        if Se>=0.99:
            Se = 0.99
        elif Se<=0.01:
            Se = 0.01
        K = Ks*Se**l*(1-(1-Se**(1/m))**m)**2
        D = K/(a*(f-qr)*m*n*(Se**(1/m+1))*(Se**(-1/m)-1)**m)
        return K, D

    def _read_ET_par(self):
        """
        read the parameters related to evaporation
        """
        #get the row number from the ind
        #j = self.ind['ET_par']
        
        #book = xlrd.open_workbook(self.input_file)
        #sheet = book.sheet_by_name('ET_par')
        ET_par = {}
        #ET_par['trans_fc'] = sheet.cell_value(j,1)
        #ET_par['trans_wp'] = sheet.cell_value(j,2)
        qr = self.shp_ens['qr']
        f = self.shp_ens['f']
        a = self.shp_ens['a']
        n = self.shp_ens['n']
        m = 1-1/n
        fl = self.shp_ens['fl']
        mid_z = self.mid_z
        ET_par['trans_fc'] = self.psi2theta(-0.33, qr, f, a, m, n)*np.exp(-mid_z/fl)
        ET_par['trans_wp'] = self.psi2theta(-15, qr, f, a, m, n)*np.exp(-mid_z/fl)
        
        self.ET_par = ET_par

if __name__=='__main__':
    #berambadi = CSGLM('/home/tomer/csglm/input/berambadi.xls')
    
    berambadi_enkf = CSGLM_ENKF('/home/tomer/csglm/input/berambadi_enkf.xls')
    
#    plt.plot(berambadi.gw_level)
#    plt.show()


       
        

        

        

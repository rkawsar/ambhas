# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 19:58:19 2011

@author: Sat Kumar Tomer
@website: www.ambhas.com
@email: satkumartomer@gmail.com

Copuled Surface-Ground water Lumped hydrological Model
"""

# import required modules
import numpy as np
import xlrd, xlwt
import os
import gdal
from gdalconst import *
from scipy.interpolate import Rbf
from Scientific.IO import NetCDF as nc


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
        root_frac = np.array(sheet.row_values(j,1))
          
        if self.no_layer != len(root_frac):
            raise ValueError('The length of the root_frac should be\
            equal to the no_layer')
        self.root_frac = root_frac
    
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
        soil_par['evap_0'] = sheet.cell_value(j,7)
        soil_par['evap_1'] = sheet.cell_value(j,8)
        self.soil_par = soil_par
    
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
        j = self.ind['ET_par']
        
        book = xlrd.open_workbook(self.input_file)
        sheet = book.sheet_by_name('ET_par')
        ET_par = {}
        ET_par['trans_1'] = sheet.col_values(j,1)
        ET_par['trans_2'] = sheet.col_values(j,2)
        ET_par['trans_3'] = sheet.col_values(j,3)
        ET_par['trans_4'] = sheet.col_values(j,4)
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
        lai = np.zeros(data_len)
        pumping = np.zeros(data_len)
    
        for i in xrange(data_len):
            year[i] = sheet.cell_value(i+1,0)
            doy[i] = sheet.cell_value(i+1,1)
            rain[i] = sheet.cell_value(i+1,2)
            pet[i] = sheet.cell_value(i+1,3)
            lai[i] = sheet.cell_value(i+1,4)
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
            
        self.lai = lai        
        

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
        self.rain_cur = self.rain[self.t]
        self.pet_cur = self.pet[self.t]
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
        In = 0.005
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
        Cm = self.runoff_par['Cm']
        B = self.runoff_par['B']
        F = 1 - (1- self.sm[:,self.t].mean()/Cm)**B 
        self.runoff_cur = self.net_rain_cur*F
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
                #K[i], D[i] = shp(max(theta_0[i],theta_0[i+1]),soil_par)
                # using the arithmatic mean of theta
                K[i], D[i] = self._shp(0.5*(self.sm[i, self.t]+self.sm[i+1, self.t]))
            else:
                K[i], D[i] = self._shp(self.sm[i,self.t])
        
        # calculate stress in soil moisture 
        self._smi_fun()
        AE = self.evap*self.SSMI
        AT = self.RZSMI*self.root_frac*self.trans
                
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
            
            # remove the water as hortonian runoff, if the soil moisture exceeds saturation
            if theta_1[0] >= self.soil_par['f']:
                HR = (theta_1[0]-self.soil_par['f'])*z[0]
                theta_1[0] = self.soil_par['f']
            else:
                HR = 0
            
            # put the result of this pixel into matrix
            self.sm[:,self.t+1] = theta_1.flatten()
            self.G = G
            self.F = F
            self.theta_1 = theta_1
            self.recharge[self.t] = Re
            self.actual_evap[self.t] = AE
            self.actual_trans[self.t] = AT.sum()
            self.horton_runoff[self.t] = HR
            
    def _smi_fun(self):
        """
        this module computes the surface soil moisture stress index, and root zone soil moisture 
        stress index
        """
        
        # calculate surface soil moisture index
        SSMI = (self.sm[0,self.t] - self.soil_par['evap_0'])/(
                self.soil_par['evap_1'] - self.soil_par['evap_0'])
        
        if SSMI > 1: 
            SSMI = 1
        elif SSMI<0:
            SSMI = 0
    
        # calculate root zone soil moisture index
        RZSMI = np.zeros((self.no_layer,))
        
        for i in range(self.no_layer):
            if (self.sm[i,self.t] < self.ET_par['trans_4']) | (self.sm[i,self.t] > self.ET_par['trans_1']):
                RZSMI[i] = 0
            elif self.sm[i,self.t] > self.ET_par['trans_2']:
                RZSMI[i] = (self.sm[i,self.t]-ET_par['trans_1'])/(self.ET_par['trans_2']\
                - ET_par['trans_1'])
            elif self.sm[i,self.t] < self.ET_par['trans_3']:
                RZSMI[i] = (theta[i,0]-self.ET_par['trans_4'])/(self.ET_par['trans_3']\
                - ET_par['trans_4'])
            else:
                RZSMI[i] = 1
        
        self.SSMI = SSMI
        self.RZSMI = RZSMI
    

    def _shp(self, theta):
        """
        soil hydraulic properties module
        """
        qr = self.soil_par['qr']
        f = self.soil_par['f']
        a = self.soil_par['a']
        n = self.soil_par['n']
        Ks = self.soil_par['Ks']
        l = self.soil_par['l']
        
        m = 1-1/n
        Se = (theta-qr)/(f - qr)
        if Se>=0.99:
            Se = 0.99
        elif Se<=0.01:
            Se = 1e-5
        K = Ks*Se**l*(1-(1-Se**(1/m))**m)**2
        D = K/(a*(f-qr)*m*n*(Se**(1/m+1))*(Se**(-1/m)-1)**m)
        return K, D


    def _gw_fun(self):
        """
        Groundwater module
        """
        F = self.gw_par['F']
        G = self.gw_par['G']
        hmin = self.gw_par['hmin']
        
        self.lam = (1-F)**2/G
        self.sy = (1-F)/G
        
        # net input = recharge - discharge
        u = self.recharge[self.t]-self.pumping_cur 
        self.gw_level[self.t+1] = F*(self.gw_level[self.t]-hmin) + G*u + hmin
        
        dzn = self.gw_level[self.t+1] - self.gw_level[self.t] 
        self.discharge = u - self.sy*(dzn) # simulated discharge
        self.z[-1] = self.z[-1] - dzn
                                   
        
        
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
        sheet.write(0,8,'AET')
        sheet.write(0,9,'recharge')
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
            sheet.write(i+1,8,self.actual_evap[i]+self.actual_trans[i])
            sheet.write(i+1,9,self.recharge[i])
            
            
        wbk.save(self.ofile_name)
        
        output_message = 'Output data writting completed sucessfully'
        self._colored_output(output_message, 32)

if __name__=='__main__':
    berambadi = CSGLM('/home/tomer/svn/ambhas/examples/berambadi.xls')
    
    

       
        

        

        

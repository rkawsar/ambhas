# -*- coding: utf-8 -*-
"""
Created on Tue Nov  1 18:57:30 2011

@author: Sat Kumar Tomer
@website: www.ambhas.com
@email: satkumartomer@gmail.com

http://nowlin.css.msu.edu/software/triangle_form.html
http://ag.arizona.edu/research/rosetta/rosetta.html#download

"""
import matplotlib.nxutils as nx
import numpy as np


class soil_texture:
    """
    Input:
        sand: percentage sand
        clay: percentage clay
    output:
        
    """
    def __init__(self, sand, clay, warning=True):
        self.sand = sand
        self.clay = clay
        
    
        soil_names = ['silty_loam', 'sand', 'silty_clay_loam', 'loam', 'clay_loam',
                      'sandy_loam', 'silty_clay', 'sandy_clay_loam', 'loamy_sand ',
                      'clay', 'silt', 'sandy_clay']
        self.soil_names = soil_names
        
        # sand, clay
        t0 = np.array([ [0,12], [0,27], [23,27], [50,0], [20,0], [8,12]], float)
        t1 = np.array([ [85,0], [90,10], [100,0]], float)
        t2 = np.array([ [0,27], [0,40], [20,40], [20,27]], float) 
        t3 = np.array([ [43,7], [23,27], [45,27], [52,20], [52,7]], float) 
        t4 = np.array([ [20,27], [20,40], [45,40], [45,27]], float)  
        t5 = np.array([ [50,0], [43,7], [52,7], [52,20], [80,20], [85,15], [70,0]], float)
        t6 = np.array([ [0,40], [0,60], [20,40]], float) 
        t7 = np.array([ [52,20], [45,27], [45,35], [65,35], [80,20]], float)
        t8 = np.array([ [70,0], [85,15], [90,10], [85,0]], float)
        t9 = np.array([ [20,40], [0,60], [0,100], [45,55], [45,40]], float) 
        t10 = np.array([ [0,0], [0,12], [8,12], [20,0]], float) 
        t11 = np.array([ [45,35], [45,55], [65,35]], float)
        
              
        #N θr θs log(α) log(n) Ks Ko L
        #-- θr -- cm3/cm3
        #-- θs -- cm3/cm3
        #-- log(α) --  log10(1/cm)
        #-- log(n) --  log10
        #-- Ks --  log(cm/day)
        #-- Ko --  log(cm/day)
        #-- L -- 
        
        shp = [[330, 0.065, 0.073, 0.439, 0.093, -2.296, 0.57, 0.221, 0.14, 1.261, 0.74, 0.243, 0.26,  0.365, 1.42],
               [308, 0.053, 0.029, 0.375, 0.055, -1.453, 0.25, 0.502, 0.18, 2.808, 0.59, 1.389, 0.24, -0.930, 0.49],
               [172, 0.090, 0.082, 0.482, 0.086, -2.076, 0.59, 0.182, 0.13, 1.046, 0.76, 0.349, 0.26, -0.156, 1.23],
               [242, 0.061, 0.073, 0.399, 0.098, -1.954, 0.73, 0.168, 0.13, 1.081, 0.92, 0.568, 0.21, -0.371, 0.84],
               [140, 0.079, 0.076, 0.442, 0.079, -1.801, 0.69, 0.151, 0.12, 0.913, 1.09, 0.699, 0.23, -0.763, 0.90],
               [476, 0.039, 0.054, 0.387, 0.085, -1.574, 0.56, 0.161, 0.11, 1.583, 0.66, 1.190, 0.21, -0.861, 0.73],
               [28,  0.111, 0.119, 0.481, 0.080, -1.790, 0.64, 0.121, 0.10, 0.983, 0.57, 0.501, 0.27, -1.287, 1.23],
               [87,  0.063, 0.078, 0.384, 0.061, -1.676, 0.71, 0.124, 0.12, 1.120, 0.85, 0.841, 0.24, -1.280, 0.99],
               [201, 0.049, 0.042, 0.390, 0.070, -1.459, 0.47, 0.242, 0.16, 2.022, 0.64, 1.386, 0.24, -0.874, 0.59],
               [84,  0.098, 0.107, 0.459, 0.079, -1.825, 0.68, 0.098, 0.07, 1.169, 0.92, 0.472, 0.26,  1.561, 1.39],
               [6,   0.050, 0.041, 0.489, 0.078, -2.182, 0.30, 0.225, 0.13, 1.641, 0.27, 0.524, 0.32,  0.624, 1.57],
               [11,  0.117, 0.114, 0.385, 0.046, -1.476, 0.57, 0.082, 0.06, 1.055, 0.89, 0.637, 0.34, -3.665, 1.80]]
        
        for i in range(12):
            exec("if nx.pnpoly(sand, clay, t0):tt=i").replace('0',str(i))
        
        if ~np.isnan(sand*clay):
            if sand+clay<100:
                self.soil_type = soil_names[tt]
                self.theta_r = shp[tt][1]
                self.theta_s = shp[tt][3]
                self.alpha = 10**shp[tt][5]*100
                self.n = 10**shp[tt][7]
                self.ks= np.exp(shp[tt][9])/100/86400
                self.l= shp[tt][13]
            else:
                if warning:
                    print("sand+clay is more than 100 percent")
                self.soil_type = np.nan
                self.theta_r = np.nan
                self.theta_s = np.nan
                self.alpha = np.nan
                self.n = np.nan
                self.ks= np.nan
                self.l= np.nan
        else:
            if warning:
                print("sand or clay contains nan")
            self.soil_type = np.nan
            self.theta_r = np.nan
            self.theta_s = np.nan
            self.alpha = np.nan
            self.n = np.nan
            self.ks= np.nan
            self.l= np.nan
    
    def get_color(self, scaling=1.0):
        """
        gives the standard soil color
        sand---> yellow
        clay---> magenta
        silt---> cyan
        
        based on the article, "TOWARDS A STANDARDISED APPROACH FOR THE 
        SELECTION OF COLOURS IN SOIL MAPS BASED ON THEIR TEXTURAL COMPOSITION 
        AND ROCK FRAGMENT ABUNDANCE: AN IMPLEMENTATION WITHIN MACROMEDIA FREEHAND"
        by Graciela Metternicht and Jasmin Goetting
        """
        # yellow magenta cyan
        ymc = {'silty_loam':(17,14,69), 'sand':(92,3,5),
               'silty_clay_loam':(10,33,57),  'loam':(43,18,39),
               'clay_loam':(33,33,34), 'sandy_loam':(65,10,25), 
               'silty_clay':(7,46,47), 'sandy_clay_loam':(58,28,14), 
               'loamy_sand':(83,6,11), 'clay':(22,59,19), 
               'silt':(7,6,87), 'sandy_clay':(51,42,7)}
        
        y, m, c = ymc[self.soil_type]
        self.y = y/100.0
        self.m = m/100.0
        self.c = c/100.0
        
        self._ymc_to_rgb(scaling)
        return self.r, self.g, self.b
        

    def _ymc_to_rgb(self, scaling):
        """
        converts ymc(yellow, magenta, cyan) to rgb (red, green, blue)
        """
        g = 0.5*(self.c+self.m+self.y - self.m)
        r = 0.5*(self.c+self.m+self.y - self.c)
        b = 0.5*(self.c+self.m+self.y - self.y)
        
        self.g = scaling*g/(r+g+b)
        self.r = scaling*r/(r+g+b)
        self.b = scaling*b/(r+g+b)

def se_fun(psi,alpha,n):
    """
    psi:    pressure head
    n:      shape index
    """
    m = 1-1/n
    se = (1+(np.abs(psi/alpha))**n)**(-m)
    return se

def wp_fun(f,qr,alpha,n):
    
    wp = qr+(f-qr)*se_fun(-150,alpha,n)
    return wp

def fc_fun(f,qr,alpha,n):
    
    fc = qr+(f-qr)*se_fun(-3.3,alpha,n)
    return fc



class saxton_rawls:
    """
    Soil Water Characteristic Estimates by Texture and Organic Matter for Hydrologic Solutions
    Input:
        sand: percentage sand
        clay: percentage clay
    output:
        
    """
    def __init__(self, sand, clay, organic_matter):
        self.S = sand
        self.C = clay 
        self.OM = organic_matter
    
    def sm_33(self):
        S = self.S
        C = self.C
        OM = self.OM
        theta_33t = -0.251*S + 0.195*C + 0.011*OM + 0.006*(S*OM) - 0.027*(C*OM) + 0.452*(S*C) +.299
        theta_33 = theta_33t + 1.283*theta_33t*2 - 0.374*theta_33t - 0.015
        print theta_33
        return theta_33
    
    def sm_s_33(self):
        S = self.S
        C = self.C
        OM = self.OM
        theta_s_33t = 0.278*S + 0.034*C + 0.022*OM -0.018*(S*OM) - 0.027*(C*OM) -0.584*(S*C) +0.078
        theta_s_33 = theta_s_33t + 0.636*theta_s_33t - 0.107
        return theta_s_33
    
    def sm_s(self):
        S = self.S
        C = self.C
        theta_33 = self.sm_33()
        theta_s_33 = self.sm_s_33()
        theta_s = theta_33 + theta_s_33 - 0.097*S + 0.043
        return theta_s
        
    def sm_s_df(self, density):
        theta_s = self.sm_s()
        theta_s_df = theta_s*(1-density/2.65)        
        return theta_s_df
        
        
        

            
if __name__=='__main__':
    sand = 20
    clay = 10
    
    foo = soil_texture(sand,clay)
    print("theta_r = %.3f"%foo.theta_r)
    
    wp = wp_fun(foo.theta_s, foo.theta_r, foo.alpha, foo.n)
    print("theta_wp = %.3f"%wp)
    sand = 49
    clay = 23
    organic_matter = 2
    foo = saxton_rawls(sand, clay, organic_matter)
    print foo.sm_s_df(1.49)
    
    
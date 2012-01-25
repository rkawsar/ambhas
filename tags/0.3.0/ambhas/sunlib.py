#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 11:53:29 2011
@author: sat kumar tomer (http://civil.iisc.ernet.in/~satkumar/)

"""

import numpy as np
import datetime as dt


class sun():
    """
    This class estimate extral-terrestial solar radiation,
    sunset time, sunrise time, daylight hours
    
    Based on the article:
        Empirical Model for Estimating Global Solar Radiation
        on Horizontal Surfaces for Selected Cities in 
        the Six Geopolitical Zones in Nigeria
    By:
        M.S. Okundamiya and A.N. Nzeako

        
    Example:
        lat_deg = 11
        lon_deg = 76
        doy = 180
        foo = sun(doy, lat_deg, lon_deg)
        hourly_etr = foo.hourly_ETR(11.0)
        daily_etr = foo.daily_ETR()
        risetime, settime = foo.set_rise()
    """
    

    def __init__(self, doy, lat_deg, lon_deg, ze=5.5):
        """ initialise the class
        Input:
            doy:            day of year
            lat_deg:        latitude in degree ( south is negative)
            lon_deg:        longitude in degree (west is negative)
            ze :            time zone in hour
        """
        self.doy = doy
        self._lat_rad = lat_deg*np.pi/180
        
        self.lon_deg = lon_deg
        self.ze = ze

        
        
        self._Isc = 1367 # solar constant (W/m^2)

        B_deg = (doy-1)*360/365
        B_rad = B_deg*np.pi/180
        
        E = 3.82*(0.000075 + 0.001868*np.cos(B_rad) - 0.032077*np.sin(B_rad) \
                    - 0.0141615*np.cos(2*B_rad) -0.04089*np.sin(2*B_rad) )
        
        self._E = E        
        
        # declination
        delta = 0.4093*np.sin(2*np.pi*(284+doy)/365)
        self._delta = delta
    
        # relative distance of the earth from sun
        dr = 1 + 0.0033*np.cos(2*np.pi*doy/365)
        self.dr = dr
        
    def hourly_ETR(self,tc):
        """
        Input:
            tc:     local time in hours
        """
        ze = self.ze
        lat_rad = self._lat_rad
        E = self._E 
        delta = self._delta
        dr = self.dr
        
        ts = tc + E + self.lon_deg/15 - ze
        # hour angle
        w = ((ts-12)*15)/180.0*np.pi
        # hourly ETR
        I0 = self._Isc*dr*(np.sin(lat_rad)*np.sin(delta) + 
                np.cos(lat_rad)*np.cos(delta)*np.cos(w))
        
        return I0
        
    def daily_ETR(self):
        """ 
        Returns the daily Extra Terrestial Radiation (ETR)
        Input:
            
        Output:
            
        """
        lat_rad = self._lat_rad
        delta = self._delta
        
        # sunset hour angle
        ws = np.arccos(-np.tan(lat_rad)*np.tan(delta))
        # maximum sunshine hour lenght
        self.N = ws*24/np.pi

        H0 = (1/np.pi)*self._Isc*self.dr*(ws*np.sin(delta)*np.sin(lat_rad) +
                np.cos(delta)*np.cos(lat_rad))
                
        return H0
    
    def set_rise(self):
        """
        Returns the sun set and rise time
        """
        lon_deg = self.lon_deg
        lat_rad = self._lat_rad
        delta = self._delta
        E = self._E
        ze = self.ze
        
        w1 = np.arccos(- np.tan(delta)*np.tan(lat_rad))
        ts1 = 12 - w1*180/np.pi/15 
        ts2 = 12 + w1*180/np.pi/15 
        
        tc1 = ts1 - E - lon_deg/15 + ze
        tc2 = ts2 - E - lon_deg/15 + ze
        
        return tc1, tc2


def EarthDistance(dn):
    """
    module to calculate the earth distance in AU
    
    Input:
        dn:    julian day
    
    Output:
        D:     distance of earth to sun in AU
    """
    thetaD = 2*np.pi*dn/365
    a0 = 1.000110; a1 = 0.034221; b1 = 0.001280; 
    a2 = 0.000719; b2 = 0.000077;
    D = np.sqrt(a0+a1*np.cos(thetaD)+b1*np.cos(thetaD)+a2*np.cos(2*thetaD)+b2*np.cos(2*thetaD));
    return D

def sun_rise_set(day,month,year,lw=-76.44,ln=11.95):
    """
    module to calculate the sunset and sunrise time
    
    Input:
        day:    day of the month (0-31)
        month:  month
        year:   year
        lw:     longitude (west positive)
        ln:     latitude (north positive)
    
    Output:
        Trise:     sunrise time in GMT+5.5
        Tset:      sunset time in GMT+5.5
        
    """
    
    Jdate = dt.date(year,month,day).toordinal()-dt.date(2000,1,1).toordinal() + 2451545
    n_star = (Jdate - 2451545 - 0.0009) - (lw/360.0)
    n = round(n_star)
    J_star = 2451545 + 0.0009 + (lw/360.0) + n
    
    M = np.mod(357.5291 + 0.98560028 * (J_star - 2451545), 360.0)
    C = (1.9148 * np.sin(M*np.pi/180)) + (0.0200 * np.sin(2 * M*np.pi/180)) + (0.0003 * np.sin(3 * M*np.pi/180))
    
    #Now, using C and M, calculate the ecliptical longitude of the sun.
    lam = np.mod(M + 102.9372 + C + 180,360)
    
    #Now there is enough data to calculate an accurate Julian date for solar noon.
    Jtransit = J_star + (0.0053 * np.sin(M*np.pi/180)) - (0.0069 * np.sin(2 * lam*np.pi/180))
    
    #To calculate the hour angle we need to find the declination of the sun
    delta = np.arcsin( np.sin(lam*np.pi/180) * np.sin(23.45*np.pi/180) )*180/np.pi
    
    #Now, calculate the hour angle, which corresponds to half of the arc length of 
    #the sun at this latitude at this declination of the sun
    H = np.arccos((np.sin(-0.83*np.pi/180) - np.sin(ln*np.pi/180) * np.sin(delta*np.pi/180)) / (np.cos(ln*np.pi/180) * np.cos(delta*np.pi/180)))*180/np.pi
    
    #Note: If H is undefined, then there is either no sunrise (in winter) or no sunset (in summer) for the supplied latitude.
    #Okay, time to go back through the approximation again, this time we use H in the calculation
    
    J_star_star = 2451545 + 0.0009 + ((H + lw)/360) + n
    #The values of M and λ from above don't really change from solar noon to sunset, so there is no need to recalculate them before calculating sunset.
    Jset = J_star_star + (0.0053 * np.sin(M*np.pi/180)) - (0.0069 * np.sin(2 * lam*np.pi/180))
    
    #Instead of going through that mess again, assume that solar noon is half-way between sunrise and sunset (valid for latitudes < 60) and approximate sunrise.
    Jrise = Jtransit - (Jset - Jtransit)
    
    Trise = np.mod(Jrise,1)*24+5.5-12
    
    Tset = np.mod(Jset,1)*24+5.5+12
    
    return Trise, Tset 

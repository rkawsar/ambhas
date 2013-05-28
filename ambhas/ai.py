# -*- coding: utf-8 -*-
"""
Created on Tue May 28 16:31:25 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

Aridity index
"""

import numpy as np


def unesco(P,ETp):
    """
    Chapter 2, Aridity and Drought, 
    R. Maliva and T. Missimer, Arid Lands Water Evaluation and Management,
    Environmental Science and Engineering, DOI: 10.1007/978-3-642-29104-3_2
    
    Input:
        P: total annual precipitation (mm)
        ETp: annual potential evapotranspiration (mm)
    Output:
        ai: aridity index
        type_climate: type of climate 
                        
    """
    ai = P/ETp

    # type of climate
    if ai<0.03:
        type_climate = 'hyper-arid'
    elif (ai>0.03) & (ai<0.20):
        type_climate = 'arid'
    elif (ai>0.20) & (ai<0.50):
        type_climate = 'semi-arid'
    elif (ai>0.50) & (ai<0.65):
        type_climate = 'dry-mildly-wet'
    elif ai>0.65:
        type_climate = 'wet'
    else:
        type_climate = None       
        
    return ai, type_climate

def thornthwaite(P_monthly, ET_monthly):
    """
    Chapter 2, Aridity and Drought, 
    R. Maliva and T. Missimer, Arid Lands Water Evaluation and Management,
    Environmental Science and Engineering, DOI: 10.1007/978-3-642-29104-3_2
    
    Input:
        P_monthly: monthly rainfall (mm)
        ET_monthly: monthly potential evapotranspiration (mm)
    Output:
        ai: aridity index        
                        
    """
    dry_months = ET_monthly>P_monthly
    d = np.sum(ET_monthly[dry_months]) - np.sum(P_monthly[dry_months])
    n = np.sum(ET_monthly[dry_months])
    ai = 100*d/n
    
    return ai
    

def de_martonne(P,Tm):
    """
    Chapter 2, Aridity and Drought, 
    R. Maliva and T. Missimer, Arid Lands Water Evaluation and Management,
    Environmental Science and Engineering, DOI: 10.1007/978-3-642-29104-3_2
    
    Input:
        P: total annual precipitation (cm)
        Tm: annual mean temperature (degree C)
    Output:
        ai: aridity index
        type_climate: type of climate 
                        
    """
    ai = P/(Tm+10)
    
    # type of climate
    if (ai>0) & (ai<5):
        type_climate = 'arid'
    elif (ai>5) & (ai<15):
        type_climate = 'semi-arid'
    elif (ai>15) & (ai<20):
        type_climate = 'dry sub-humid'
    elif (ai>20) & (ai<30):
        type_climate = 'moist sub-humid'
    elif (ai>30) & (ai<60):
        type_climate = 'wet'
    elif ai>60:
        type_climate = 'humid'   
    else:
        type_climate = None   
                    
    return ai, type_climate
    
if __name__ == '__main__':
    # de_martonne
    P = np.random.uniform(100)
    Tm = np.random.uniform(30)
    print de_martonne(P,Tm)
    
    # unesco
    ETp = np.random.uniform(100)
    print unesco(P,ETp)
    
    # thornthwaite
    P_monthly = np.random.rand(12)
    ET_monthly = 10*np.random.rand(12)
    print thornthwaite(P_monthly, ET_monthly)
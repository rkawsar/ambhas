# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 14:51:35 2012

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

import numpy as np
from ambhas.copula import Copula  
import matplotlib.pyplot as plt

x = np.random.uniform(size=(100))
y = np.log(x) + 0.5*np.random.normal(size=(100))
  
foo = Copula(x, y, 'clayton')
foo.tau

x1,y1 = foo.generate_xy()

plt.figure(figsize=(6, 4.5))
plt.scatter(x1,y1, color='g', label='Generated ensemble')  
plt.scatter(x,y, color='r', label='Observations')  
plt.xlabel('x')  
plt.ylabel('y')
plt.legend(loc='best')
plt.savefig('/home/tomer/svn/ambhas-wiki/images/copula.png')  

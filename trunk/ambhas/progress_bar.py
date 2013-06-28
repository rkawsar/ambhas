# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 17:30:18 2013

@author: Sat Kumar Tomer
@email: satkumartomer@gmail.com
@website: www.ambhas.com

"""

import numpy as np

class PB:
    
    def __init__(self, n, txt='Processing', pyton_ind=True):
        self.n = n
        self.txt = txt
        self.i = 0
        
        self.i_print = np.round(0.01*np.arange(2,100,3)*n)
        
        
    
    def grass(self):
        """
        GRASS like progress bar
        2% 5% .....  95%   98% 
        """
                
        n = self.n
        i_print = self.i_print
                
        if self.i==0:
            print('Started! %s'%self.txt)
        elif self.i==n-1:
            print('\nFinished! %s'%self.txt)
        elif self.i in i_print:
            #print i
            print('%s%%  '%np.round(100*self.i/n)),
        
        self.i +=1

if __name__ == '__main__':
    n = 786
    foo = PB(n)
    for i in range(n):
        foo.grass()
    
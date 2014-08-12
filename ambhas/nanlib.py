'''
Created on Aug 12, 2014

@author: tomers
'''

import numpy as np


def filter_nan_matrix(mat):
    """
    filter the nan data

    Input
        mat : np.array
    Output
        None
    """
    return mat[~np.isnan(np.sum(mat, axis=1)), :]


def create_nan(shape):
    """
    create a nan array

    create a nan array of the size shape

    Input:
        shape: tuple
            shape of the return np.array
    Output:
        mat: np.array
            a np.array filled with nans
    """
    mat = np.empty(shape)
    mat[:] = np.nan
    return mat


if __name__ == '__main__':
    mat = np.random.rand(100, 5)

    mat[mat < 0.05] = np.nan

    mat = filter_nan_matrix(mat)
    
    print('processing over')

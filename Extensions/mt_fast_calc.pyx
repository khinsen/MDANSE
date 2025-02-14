# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Extensions/mt_fast_calc.pyx
# @brief     Implements module/class/test mt_fast_calc
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import cython
cimport numpy as np 
import numpy as np
from numpy cimport ndarray

cdef extern from "math.h":
    double floor(double x)
    double ceil(double x)

@cython.boundscheck(False)
@cython.wraparound(False)
def mt(ndarray[np.float64_t, ndim = 2] config not None,
       ndarray[np.int32_t, ndim = 3] grid not None,
       double resolution,ndarray[np.float64_t, ndim = 1] mini not None): 
    
    cdef int at, nbatom, atom, i, j, k
    cdef double Xpos, Ypos, Zpos, mx, my, mz
    
    mx = mini[0] 
    my = mini[1]
    mz = mini[2]
    
    nbatom = config.shape[0]
    for atom in range(nbatom):
        # The  of atoms |i| in the current configuration.
        i = int(floor((config[atom,0]-mx)/resolution))
        j = int(floor((config[atom,1]-my)/resolution))
        k = int(floor((config[atom,2]-mz)/resolution))
        grid[i][j][k] += 1

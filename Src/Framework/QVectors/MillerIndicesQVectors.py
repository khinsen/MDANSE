# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/MillerIndicesQVectors.py
# @brief     Implements module/class/test MillerIndicesQVectors
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors

class MillerIndicesLatticeQVectors(LatticeQVectors):
    """
    """
    
    settings = collections.OrderedDict()
    settings['shells'] = ('range', {"valueType":float, "includeLast":True, "mini":0.0})
    settings['width'] = ('float', {"mini":1.0e-6, "default":1.0})
    settings['h'] = ('range', {"includeLast":True})
    settings['k'] = ('range', {"includeLast":True})
    settings['l'] = ('range', {"includeLast":True})

    def _generate(self):
                
        hSlice = slice(self._configuration["h"]["first"],self._configuration["h"]["last"]+1,self._configuration["h"]["step"])
        kSlice = slice(self._configuration["k"]["first"],self._configuration["k"]["last"]+1,self._configuration["k"]["step"])
        lSlice = slice(self._configuration["l"]["first"],self._configuration["l"]["last"]+1,self._configuration["l"]["step"])

        # The hkl matrix (3,n_hkls)                
        hkls = numpy.mgrid[hSlice,kSlice,lSlice]
        hkls = hkls.reshape(3,hkls.size/3)
                
        # The k matrix (3,n_hkls)
        vects = numpy.dot(self._reciprocalMatrix,hkls)
        
        dists2 = numpy.sum(vects**2,axis=0)
                
        halfWidth = self._configuration["width"]["value"]/2

        if self._status is not None:
            self._status.start(len(self._configuration["shells"]["value"]))

        self._configuration["q_vectors"] = collections.OrderedDict()
        
        for q in self._configuration["shells"]["value"]:

            qmin = max(0,q - halfWidth)
                                    
            q2low = qmin*qmin
            q2up = (q + halfWidth)*(q + halfWidth)
            
            hits = numpy.where((dists2 >= q2low) & (dists2 <= q2up))[0]            

            nHits = len(hits)

            if nHits != 0:         
                self._configuration["q_vectors"][q] = {}
                self._configuration["q_vectors"][q]['q_vectors'] = vects[:,hits]
                self._configuration["q_vectors"][q]['n_q_vectors'] = nHits
                self._configuration["q_vectors"][q]['q'] = q
                self._configuration["q_vectors"][q]['hkls'] = numpy.rint(numpy.dot(self._invReciprocalMatrix,self._configuration["q_vectors"][q]['q_vectors']))

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()

REGISTRY["miller_indices_lattice"] = MillerIndicesLatticeQVectors

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/SphericalQVectors.py
# @brief     Implements module/class/test SphericalQVectors
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
from MDANSE.Mathematics.Geometry import random_points_on_sphere
from MDANSE.Framework.QVectors.IQVectors import IQVectors

class SphericalQVectors(IQVectors):
    """
    """
    
    settings = collections.OrderedDict()
    settings['seed'] = ('integer', {"mini":0, "default":0})
    settings['shells'] = ('range', {"valueType":float, "includeLast":True, "mini":0.0})
    settings['n_vectors'] = ('integer', {"mini":1, "default":50})
    settings['width'] = ('float', {"mini":0.0, "default":1.0})
    
    def _generate(self):

        if self._configuration["seed"]["value"] != 0:           
            numpy.random.seed(self._configuration["seed"]["value"])

        width = self._configuration["width"]["value"]

        nVectors = self._configuration["n_vectors"]["value"]

        self._configuration["q_vectors"] = collections.OrderedDict()
        
        if self._status is not None:
            self._status.start(len(self._configuration["shells"]["value"]))

        for q in self._configuration["shells"]["value"]:

            fact = q*numpy.sign(numpy.random.uniform(-0.5,0.5,nVectors)) + width*numpy.random.uniform(-0.5,0.5,nVectors)

            v = random_points_on_sphere(radius=1.0, nPoints=nVectors)
            
            self._configuration["q_vectors"][q] = {}
            self._configuration["q_vectors"][q]['q_vectors'] = fact*v
            self._configuration["q_vectors"][q]['n_q_vectors'] = nVectors
            self._configuration["q_vectors"][q]['q'] = q
            self._configuration["q_vectors"][q]['hkls'] = None

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()

REGISTRY["spherical"] = SphericalQVectors

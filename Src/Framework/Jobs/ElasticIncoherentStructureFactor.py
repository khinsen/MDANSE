# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/ElasticIncoherentStructureFactor.py
# @brief     Implements module/class/test ElasticIncoherentStructureFactor
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
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.MolecularDynamics.Trajectory import read_atoms_trajectory

class ElasticIncoherentStructureFactor(IJob):
    """
    The Elastic Incoherent Structure Factor (EISF ) is defined as the limit of the incoherent
    intermediate scattering function for infinite time.

    The EISF appears as the incoherent amplitude of the elastic line in the neutron scattering spectrum.
    Elastic scattering is only present for systems in which the atomic motion is confined in space, as
    in solids. The Q-dependence of the EISF indicates e.g. the fraction of static/mobile atoms and the spatial dependence of the dynamics.
    """
    
    label = "Elastic Incoherent Structure Factor"

    # The category of the analysis.
    category = ('Analysis','Scattering',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['q_vectors'] = ('q_vectors', {'dependencies':{'trajectory':'trajectory'}})
    settings['projection'] = ('projection', {'label':"project coordinates"})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['weights'] = ('weights', {'default':'b_incoherent',"dependencies":{"atom_selection":"atom_selection"}})
    settings['output_files'] = ('output_files', {'formats':["hdf","netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        
        self.numberOfSteps = self.configuration['atom_selection']['selection_length']

        self._nQShells = self.configuration["q_vectors"]["n_shells"]
                
        self._nFrames = self.configuration['frames']['number']
                
        self._outputData.add("q","line", self.configuration["q_vectors"]["shells"], units="1/nm") 
                        
        for element in self.configuration['atom_selection']['unique_names']:
            self._outputData.add("eisf_%s" % element,"line", (self._nQShells,), axis="q", units="au")                                                 

        self._outputData.add("eisf_total","line", (self._nQShells,), axis="q", units="au")                                                 
        
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. atomicEISF (numpy.array): The atomic elastic incoherent structure factor
        """

        # get atom index
        indexes = self.configuration['atom_selection']["indexes"][index]
        masses = self.configuration['atom_selection']["masses"][index]
                
        series = read_atoms_trajectory(self.configuration["trajectory"]["instance"],
                                       indexes,
                                       first=self.configuration['frames']['first'],
                                       last=self.configuration['frames']['last']+1,
                                       step=self.configuration['frames']['step'],
                                       weights=masses)
        
        series = self.configuration['projection']["projector"](series)

        atomicEISF = numpy.zeros((self._nQShells,), dtype=numpy.float64)

        for i,q in enumerate(self.configuration["q_vectors"]["shells"]):
            
            if not q in self.configuration["q_vectors"]["value"]:
                continue

            qVectors = self.configuration["q_vectors"]["value"][q]["q_vectors"]
            
            a = numpy.average(numpy.exp(1j * numpy.dot(series, qVectors)),axis=0)
            a = numpy.abs(a)**2
            
            atomicEISF[i] = numpy.average(a)
            
        return index, atomicEISF
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        # The symbol of the atom.
        element = self.configuration['atom_selection']["names"][index]
        
        self._outputData["eisf_%s" % element] += x
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()        
        for element, number in nAtomsPerElement.items():
            self._outputData["eisf_%s" % element][:] /= number

        weights = self.configuration["weights"].get_weights()        
        self._outputData["eisf_total"][:] = weight(weights,self._outputData,nAtomsPerElement,1,"eisf_%s")
            
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['eisf'] = ElasticIncoherentStructureFactor

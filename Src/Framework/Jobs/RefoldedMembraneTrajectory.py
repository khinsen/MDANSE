# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/RefoldedMembraneTrajectory.py
# @brief     Implements module/class/test RefoldedMembraneTrajectory
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os

from MMTK.Collections import Collection
from MMTK.ParticleProperties import Configuration
from MMTK.Trajectory import SnapshotGenerator, Trajectory, TrajectoryOutput

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.Mathematics.Geometry import center

class RefoldedMembraneTrajectory(IJob):
    """
    Rebuild the trajectory of a membrane such that the lipids in the upper leaflet are actually in the upper half of the simulation box 
    and therefore the lipids in the lower leaflet are in the lower half of the box i.e. the membrane is centred in the simulation box.
    
    :note: The normal to the membrane is assumed to be parallel to the z axis. 
    """
        
    label = "Refolded Membrane Trajectory"

    category = ('Analysis','Macromolecules','Lipids')
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{'default':os.path.join('..','..','..','Data','Trajectories','MMTK','dmpc_in_periodic_universe.nc')})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['axis'] = ('single_choice', {'label':"membrane axis", 'choices':['a','b','c'], 'default':'c'})
    settings['upper_leaflet'] = ('string', {'label':"name of the lipid of the upper leaflet", 'default':"DMPC"})
    settings['lower_leaflet'] = ('string', {'label':"name of the lipid of the lower leaflet", 'default':"DMPC"})
    settings['output_files'] = ('output_files', {'formats':["netcdf"]})
                
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration['frames']['number']
        
        self._universe = self.configuration['trajectory']['instance'].universe
        
        self._upperLeaflet = Collection([obj for obj in self._universe.objectList() if obj.name == self.configuration["upper_leaflet"]["value"]])
        self._lowerLeaflet = Collection([obj for obj in self._universe.objectList() if obj.name == self.configuration["lower_leaflet"]["value"]])
        self._membrane = Collection(self._upperLeaflet,self._lowerLeaflet)
        
        if (not self._membrane):
            raise JobError('No objects matching a lipid membrane could be found in the universe.')
            
        self._upperLeafletIndexes = [at.index for at in self._upperLeaflet.atomList()]
        self._lowerLeafletIndexes = [at.index for at in self._lowerLeaflet.atomList()]
        self._membraneIndexes = [at.index for at in self._membrane.atomList()]
        
        # The output trajectory is opened for writing.
        self._rmt = Trajectory(self._membrane, self.configuration['output_files']['files'][0], "w")
        
        # The title for the trajectory is set. 
        self._rmt.title = self.__class__.__name__

        # Create the snapshot generator.
        self._snapshot = SnapshotGenerator(self._universe, actions = [TrajectoryOutput(self._rmt, "all", 0, None, 1)])

        self._axis = self.configuration["axis"]["index"]                

    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. None
        """

        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index]
              
        # The configuration corresponding to this index is set to the universe.
        self._universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)

        conf = self._universe.contiguousObjectConfiguration()

        boxCoords = self._universe._realToBoxPointArray(conf.array)

        # Compute the center of gravity of the whole lower leaflet.
        lowerLeafletCenter = center(boxCoords[self._lowerLeafletIndexes,:])[self._axis]
        for lip in self._upperLeaflet:
            idxs = [at.index for at in lip.atomList()]
            currCenter = center(boxCoords[idxs,:])[self._axis]
            if currCenter < lowerLeafletCenter:
                boxCoords[idxs,2] += 1.0 

        upperLeafletCenter = center(boxCoords[self._upperLeafletIndexes,:])[self._axis]
        for lip in self._lowerLeaflet:
            idxs = [at.index for at in lip.atomList()]
            currCenter = center(boxCoords[idxs,:])[self._axis]
            if currCenter > upperLeafletCenter:
                boxCoords[idxs,2] -= 1.0

        conf = Configuration(self._universe, self._universe._boxToRealPointArray(boxCoords))
        
        self._universe.setConfiguration(conf)
                          
        # The times corresponding to the running index.
        t = self.configuration['frames']['time'][index]
        
        # A snapshot of the universe is written to the output trajectory.
        self._snapshot(data = {'time': t})
                                
        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """   
        pass
        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """ 
        # The input trajectory is closed.
        self.configuration['trajectory']['instance'].close()
                                                    
        # The output trajectory is closed.
        self._rmt.close()
        
REGISTRY['rmt'] = RefoldedMembraneTrajectory

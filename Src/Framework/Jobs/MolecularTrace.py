# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/MolecularTrace.py
# @brief     Implements module/class/test MolecularTrace
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
from MDANSE.Extensions import mt_fast_calc

class MolecularTrace(IJob):
    """
    A Molecular Trace is a time-integrated trace of selected atoms in terms of their coordinates.
    
    * the minimal and maximal coordinates from the selected atomic trajectories are computed.
    * based on these min/max and a spatial resolution, a cartesian grid is constructed.
    * for each atom and for each frame of the selected trajectories, a histogram of presence, called the spatial density, is constructed.

    The molecular trace can reveal anisotropic vibrations and diffusion pathways.	
    
    **Acknowledgement and publication:**\n
    Gael Goret, PELLEGRINI Eric
    
    """

    label = "Molecular Trace"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['spatial_resolution'] = ('float', {'mini':0.01, 'default':0.1})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
    
    def initialize(self):

        self.numberOfSteps = self.configuration['frames']['number']

        # Will store the time.
        self._outputData.add('time',"line",self.configuration['frames']['time'],units="ps")
        
        # Generate the grids that will be used to quantify the presence of atoms in an area.
        self.resolution = self.configuration['spatial_resolution']['value']   
                
        maxx, maxy, maxz = 0,0,0
        minx, miny, minz = 10**9,10**9,10**9
        for i in range(self.numberOfSteps):
            frameIndex = self.configuration['frames']['value'][i]
            self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
            conf = self.configuration['trajectory']['instance'].universe.contiguousObjectConfiguration()
            
            minx_loc = conf.array[:,0].min()
            miny_loc = conf.array[:,1].min()
            minz_loc = conf.array[:,2].min()
             
            maxx_loc = conf.array[:,0].max()
            maxy_loc = conf.array[:,1].max()
            maxz_loc = conf.array[:,2].max()
            
            maxx = max(maxx_loc, maxx)
            maxy = max(maxy_loc, maxy)
            maxz = max(maxz_loc, maxz)
            
            minx = min(minx, minx_loc)
            miny = min(miny, miny_loc)
            minz = min(minz, minz_loc)
            
        dimx = maxx - minx
        dimy = maxy - miny
        dimz = maxz - minz
            
        self.min = numpy.array([minx, miny, minz], dtype = numpy.float64)
        self._outputData.add('origin',"line", self.min, units = 'nm')
        
        self.gdim = numpy.ceil(numpy.array([dimx, dimy, dimz])/self.resolution).astype(numpy.int)
        spacing = self.configuration['spatial_resolution']['value']
        self._outputData.add('spacing',"line",numpy.array([spacing, spacing, spacing]), units = 'nm')
        self.grid = numpy.zeros(self.gdim, dtype = numpy.int32)

        self._outputData.add('molecular_trace',"volume", tuple(numpy.ceil(numpy.array([dimx, dimy, dimz])/self.resolution).astype(numpy.int)))
        
        self._indexes  = [idx for idxs in self.configuration['atom_selection']['indexes'] for idx in idxs]
        
    def run_step(self, index):
        """
        Runs a single step of the job.
        
        @param index: the index of the step.
        @type index: int.      
        """
        
        # This is the actual index of the frame corresponding to the loop index.
        frameIndex = self.configuration['frames']['value'][index]
                            
        # The configuration corresponding to this index is set to the universe.
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
        
        conf = self.configuration['trajectory']['instance'].universe.contiguousObjectConfiguration()

        grid = numpy.zeros(self.gdim, dtype = numpy.int32)

        # Loop over the indexes of the selected atoms for the molecular trace calculation.
        mt_fast_calc.mt(conf.array[self._indexes,:], grid, self.configuration['spatial_resolution']['value'], self.min)

        return index, grid
    
    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.
        
        @param x: the output of run_step method.
        @type x: no specific type.
        """

        numpy.add(self.grid,x,self.grid)
    
    def finalize(self):
        """
        Finalize the job.
        """
        
        self._outputData['molecular_trace'][:] = self.grid
                
        # Write the output variables.
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
REGISTRY['mt'] = MolecularTrace
        

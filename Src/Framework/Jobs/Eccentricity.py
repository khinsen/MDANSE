# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Eccentricity.py
# @brief     Implements module/class/test Eccentricity
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

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass

class Eccentricity(IJob):
    """
    Computes the eccentricity for a set of atoms e.g. in a micelle.\n

    **Calculation:** \n
    Eccentricity is calculated using the principal axes of inertia 'I' along x, y and z: \n   
    .. math:: Eccentricity = 1-\\frac{I_{min}}{I_{average}}
    
    The ratio of largest to smallest is  \n
    .. math:: ratio = \\frac{Imax}{Imin}
    
    The semiaxes a,b and c are those of an ellipsoid \n
    .. math:: semiaxis_a = \\sqrt{ \\frac{5}{2M} (I_{max}+I_{mid}-I_{min}) }
    .. math:: semiaxis_b = \\sqrt{ \\frac{5}{2M} (I_{max}+I_{min}-I_{mid}) }
    .. math:: semiaxis_c = \\sqrt{ \\frac{5}{2M} (I_{mid}+I_{min}-I_{max}) }
    
    Where:\n
        - M is the total mass of all the selected atoms
        - :math:`I_{min}` , :math:`I_{mid}` and :math:`I_{max}` are respectively the smallest, middle and biggest inertia moment values
        

    **Output:** \n   
    #. moment_of_inertia_xx: the moment of inertia in x direction acting on the surface element with its vector normal in x direction
    #. moment_of_inertia_xy: the moment of inertia in y direction acting on the surface element with its vector normal in x direction
    #. moment_of_inertia_xz: the moment of inertia in z direction acting on the surface element with its vector normal in x direction
    #. moment_of_inertia_yy: the moment of inertia in y direction acting on the surface element with its vector normal in y direction
    #. moment_of_inertia_yz: the moment of inertia in z direction acting on the surface element with its vector normal in y direction
    #. moment_of_inertia_zz: the moment of inertia in z direction acting on the surface element with its vector normal in z direction
    #. semiaxis_a: ellipse biggest axis
    #. semiaxis_b: ellipse middle axis
    #. semiaxis_c: ellipse smallest axis
    #. ratio_of_largest_to_smallest
    #. eccentricity
    #. radius_of_gyration
    
   
    **Usage:** \n
    This analysis can be used to study macro-molecular geometry and sphericity .
    It was originally conceived to calculate the ellipticity of micelles.
    
    **Acknowledgement and publication:**\n
    AOUN Bachir, PELLEGRINI Eric
    
    """
    
    label = "Eccentricity"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['center_of_mass'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['weights']=('weights',{"dependencies":{"atom_selection":"atom_selection"}})
    settings['output_files'] = ('output_files', {'formats':["hdf","netcdf","ascii"]})
            
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        self.numberOfSteps = self.configuration['frames']['number']
                       
        self._masses = [m for masses in self._configuration['atom_selection']['masses'] for m in masses]
        self._totalMass = numpy.sum(self._masses)
                
        # Will store the time.
        self._outputData.add('time',"line", self.configuration['frames']['time'], units="ps")
        
        npoints = numpy.zeros((self.configuration['frames']['number']), dtype=numpy.float64)
        
        for axis in ['xx','xy','xz','yy','yz','zz']:
            self._outputData.add('moment_of_inertia_%s' %axis,"line",npoints,axis='time',units="uma*nm2")
        for axis in ['a','b','c']:
            self._outputData.add('semiaxis_%s' %axis,"line",npoints,axis='time',units="nm")
 
        self._outputData.add('eccentricity',"line",npoints,axis='time') 
        
        self._outputData.add('ratio_of_largest_to_smallest',"line",npoints,axis='time') 
        
        self._outputData.add('radius_of_gyration',"line",npoints,axis='time')
        
        self._indexes = self.configuration['atom_selection'].get_indexes()
    
    def run_step(self, index):
        """
        Runs a single step of the job.\n
 
        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step. 
            #. moment_of_inertia_xx (numpy.array)
            #. moment_of_inertia_xy (numpy.array)
            #. moment_of_inertia_xz (numpy.array)
            #. moment_of_inertia_yy (numpy.array)
            #. moment_of_inertia_yz (numpy.array)
            #. moment_of_inertia_zz (numpy.array)
            #. radius_of_gyration (numpy.array)
        """
        # get the Frame index
        frameIndex = self.configuration['frames']['value'][index]  
        self.configuration['trajectory']['instance'].universe.setFromTrajectory(self.configuration['trajectory']['instance'], frameIndex)
        
        # read frame atoms coordinates                                                                             
        series = self.configuration['trajectory']['instance'].universe.configuration().array

        com = center_of_mass(series[self.configuration['center_of_mass']['flatten_indexes']],
                             masses=numpy.array(self.configuration['center_of_mass']['masses']).flatten())

        # calculate the inertia moments and the radius of gyration
        xx = xy = xz = yy = yz = zz = 0
        for name, idxs in self._indexes.items():
            atomsCoordinates = series[idxs,:]
            difference = atomsCoordinates-com
            
            w = ELEMENTS[name,self.configuration["weights"]["property"]]
                                            
            xx += numpy.add.reduce(w * (difference[:,1]*difference[:,1] + difference[:,2]*difference[:,2]) )
            xy -= numpy.add.reduce(w * (difference[:,0]*difference[:,1]) )
            xz -= numpy.add.reduce(w * (difference[:,0]*difference[:,2]) )
            
            yy += numpy.add.reduce(w * (difference[:,0]*difference[:,0] + difference[:,2]*difference[:,2]) )
            yz -= numpy.add.reduce(w * (difference[:,1]*difference[:,2]) )
            
            zz += numpy.add.reduce(w * (difference[:,0]*difference[:,0] + difference[:,1]*difference[:,1]) )

        rog =  numpy.sum( (series-com)**2 )
        
        
        return index, (xx ,xy, xz, yy, yz, zz, rog)
    
    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        
        Imin = min(x[0], x[3], x[5])
        Imax = max(x[0], x[3], x[5])
        Imid = [x[0], x[3], x[5]]
        Imid.pop(Imid.index(Imin))
        Imid.pop(Imid.index(Imax))
        Imid = Imid[0]
        
        average = (x[0]+x[3]+x[5]) / 3 
        
        # moment of inertia
        self._outputData['moment_of_inertia_xx'][index] = x[0]
        self._outputData['moment_of_inertia_xy'][index] = x[1]
        self._outputData['moment_of_inertia_xz'][index] = x[2]
        self._outputData['moment_of_inertia_yy'][index] = x[3]
        self._outputData['moment_of_inertia_yz'][index] = x[4]
        self._outputData['moment_of_inertia_zz'][index] = x[5]          
        
        # eccentricity = 0 for spherical objects
        self._outputData['eccentricity'][index] = 1-Imin/average
        
        # ratio_of_largest_to_smallest = 1 for spherical objects
        self._outputData['ratio_of_largest_to_smallest'][index] = Imax/Imin
        
        # semiaxis
        self._outputData["semiaxis_a"][index] = numpy.sqrt( 5.0/(2.0*self._totalMass) * (Imax+Imid-Imin) ) 
        self._outputData["semiaxis_b"][index] = numpy.sqrt( 5.0/(2.0*self._totalMass) * (Imax+Imin-Imid) ) 
        self._outputData["semiaxis_c"][index] = numpy.sqrt( 5.0/(2.0*self._totalMass) * (Imid+Imin-Imax) )

        # radius_of_gyration is a measure of the distribution of the mass 
        # of atomic groups or molecules that constitute the aqueous core 
        # relative to its center of mass 
        self._outputData['radius_of_gyration'][index] = numpy.sqrt(x[6]/self.configuration['atom_selection']['selection_length'] )
        
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """   

        # Write the output variables.
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()
        
REGISTRY['ecc'] = Eccentricity
     

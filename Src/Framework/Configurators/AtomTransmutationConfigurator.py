# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/AtomTransmutationConfigurator.py
# @brief     Implements module/class/test AtomTransmutationConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import ELEMENTS, REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
from MDANSE.Framework.AtomSelectionParser import AtomSelectionParser
        
class AtomTransmutationConfigurator(IConfigurator):
    """
    This configurator allows to define a set of atoms to be transmutated to a given chemical
    element.
    
    For some analysis it can be necessary to change the nature of the chemical element of a given
    part of the system to have results closer to experience. A good example is to change some 
    hydrogen atoms to deuterium in order to fit with experiments where deuteration experiments have 
    been performed for improving the contrast and having a better access to the dynamic of a specific part
    of the molecular system.
            
    :note: this configurator depends on 'trajectory' and 'atom_selection' configurators to be configured
    """
        
    _default = None
                                
    def configure(self, value):
        '''
        Configure an input value. 
        
        The value can be:
        
        #. ``None``: no transmutation is performed
        #. (str,str)-dict: for each (str,str) pair, a transmutation will be performed by parsing \
        the 1st element as an atom selection string and transmutating the corresponding atom \
        selection to the target chemical element stored in the 2nd element
        #. str: the transmutation will be performed by reading the corresponding user definition
        
        :param value: the input value
        :type value: None or (str,str)-dict or str 
        '''

        self["value"] = value
                        
        # if the input value is None, do not perform any transmutation
        if value is None:
            return
        
        if not isinstance(value,(list,tuple)):
            raise ConfiguratorError("Invalid input value.")

        trajConfig = self._configurable[self._dependencies['trajectory']]
                                                                
        parser = AtomSelectionParser(trajConfig["instance"])        

        self._nTransmutatedAtoms = 0

        for expression,element in value:
                  
            # Otherwise, it must be a string that will be found as a user-definition keys
            if not isinstance(expression,basestring):
                raise ConfiguratorError("Wrong format for atom transmutation configurator.",self)
                
            if UD_STORE.has_definition(trajConfig["basename"],"atom_selection",expression):                
                ud = UD_STORE.get_definition(trajConfig["basename"],"atom_selection",expression)
                indexes = ud["indexes"]
            else:
                indexes = parser.parse(expression)
                
            self.transmutate(indexes, element)
            
            self._nTransmutatedAtoms += len(indexes)
                
    def transmutate(self, selection, element):
        '''
        Transmutates a set of atoms to a given element 
        
        :param selection: the indexes of the atoms to be transmutated
        :type selection: list of int
        :param element: the symbol of the element to which the selected atoms should be transmutated
        :type element: str
        '''
        
        if element not in ELEMENTS:
            raise ConfiguratorError("the element %r is not registered in the database" % element, self)

        atomSelConfigurator = self._configurable[self._dependencies['atom_selection']]
                        
        for idx in selection:
            try:
                idxInSelection = atomSelConfigurator["flatten_indexes"].index(idx)
            except ValueError:
                pass
            else:                 
                atomSelConfigurator["names"][idxInSelection] = element
                atomSelConfigurator["elements"][idxInSelection] = [element]

        atomSelConfigurator['unique_names'] = sorted(set(atomSelConfigurator['names']))
        atomSelConfigurator['masses'] = [[ELEMENTS[n,'atomic_weight']] for n in atomSelConfigurator['names']]
            
    def get_information(self):
        '''
        Returns some informations the atoms selected for being transmutated.
        
        :return: the information about the atoms selected for being transmutated.
        :rtype: str
        '''

        if not self.has_key("value"):
            return "Not configured yet"
                
        if self["value"] is None:
            return "No atoms selected for transmutation"
        
        return "Number of transmutated atoms:%d\n" % self._nTransmutatedAtoms
    
REGISTRY["atom_transmutation"] = AtomTransmutationConfigurator

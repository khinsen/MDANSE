# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/NAMD.py
# @brief     Implements module/class/test NAMD
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.DCDConverter import DCDConverter

class NAMDConverter(DCDConverter):
    """
    Converts a NAMD trajectory to a MMTK trajectory.
    """
    
    label = "NAMD"

REGISTRY['namd'] = NAMDConverter

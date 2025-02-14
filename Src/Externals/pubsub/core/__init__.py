# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/core/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""
Core package of pubsub, holding the publisher, listener, and topic
object modules. Functions defined here are used internally by
pubsub so that the right modules can be found later, based on the
selected messaging protocol.

Indeed some of the API depends on the messaging
protocol used. For instance sendMessage(), defined in publisher.py,
has a different signature (and hence implementation) for the kwargs
protocol than for the arg1 protocol.

The most convenient way to
support this is to put the parts of the package that differ based
on protocol in separate folder, and add one of those folders to
the package's __path__ variable (defined automatically by the Python
interpreter when __init__.py is executed). For instance, code
specific to the kwargs protocol goes in the kwargs folder, and code
specific to the arg1 protocol in the arg1 folder. Then when doing
"from pubsub.core import listener", the correct listener.py will be
found for the specified protocol. The default protocol is kwargs.

Only one protocol can be used in an application. The default protocol,
if none is chosen by user, is kwargs, as selected by the call to
_prependModulePath() at end of this file. 

:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE_BSD_Simple.txt for details.

"""
    

def _prependModulePath(extra):
    """Insert extra at beginning of package's path list. Should only be
    called once, at package load time, to set the folder used for
    implementation specific to the default message protocol."""
    corepath = __path__
    initpyLoc = corepath[-1]
    import os
    corepath.insert(0, os.path.join(initpyLoc, extra))

# add appropriate subdir for protocol-specific implementation
from .. import policies
_prependModulePath(policies.msgDataProtocol)

from .publisher import Publisher

from .callables import (
    AUTO_TOPIC,
)

from .listener import (
    Listener,
    getID as getListenerID,
    ListenerMismatchError,
    IListenerExcHandler,
)

from .topicobj import (
    Topic,
    SenderMissingReqdMsgDataError, 
    SenderUnknownMsgDataError, 
    MessageDataSpecError, 
    TopicDefnError, 
    ExcHandlerError,
)

from .topicmgr import (
    TopicManager, 
    TopicDefnError,
    TopicNameError,
    ALL_TOPICS,
)

from .topicdefnprovider import (
    ITopicDefnProvider,
    TopicDefnProvider,
    ITopicDefnDeserializer,
    UnrecognizedSourceFormatError, 
    
    exportTopicTreeSpec,
    TOPIC_TREE_FROM_MODULE,
    TOPIC_TREE_FROM_STRING,
    TOPIC_TREE_FROM_CLASS, 
)

from .topictreetraverser import (
    TopicTreeTraverser,
)

from .notificationmgr import (
    INotificationHandler,
)
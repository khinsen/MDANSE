# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/utils/topictreeprinter.py
# @brief     Implements module/class/test topictreeprinter
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""
Output various aspects of topic tree to string or file.

:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE_BSD_Simple.txt for details.
"""

from textwrap import TextWrapper

from ..core.topictreetraverser import (ITopicTreeVisitor, TopicTreeTraverser)


class TopicTreePrinter(ITopicTreeVisitor):
    """
    Example topic tree visitor that prints a prettified representation
    of topic tree by doing a depth-first traversal of topic tree and
    print information at each (topic) node of tree. Extra info to be
    printed is specified via the 'extra' kwarg. Its value must be a
    list of characters, the order determines output order:
    - D: print description of topic
    - a: print kwarg names only
    - A: print topic kwargs and their description
    - L: print listeners currently subscribed to topic

    E.g. TopicTreePrinter(extra='LaDA') would print, for each topic,
    the list of subscribed listeners, the topic's list of kwargs, the
    topic description, and the description for each kwarg,

        >>> Topic "delTopic"
           >> Listeners:
              > listener1_2880 (from yourModule)
              > listener2_3450 (from yourModule)
           >> Names of Message arguments:
              > arg1
              > arg2
           >> Description: whenever a topic is deleted
           >> Descriptions of Message arguments:
              > arg1: (required) its description
              > arg2: some other description

    """

    allowedExtras = frozenset('DAaL') # must NOT change
    ALL_TOPICS_NAME = 'ALL_TOPICS'    # output for name of 'all topics' topic

    def __init__(self, extra=None, width=70, indentStep=4,
        bulletTopic='\\--', bulletTopicItem='|==', bulletTopicArg='-', fileObj=None):
        """Topic tree printer will print listeners for each topic only
        if printListeners is True. The width will be used to limit
        the width of text output, while indentStep is the number of
        spaces added each time the text is indented further. The
        three bullet parameters define the strings used for each
        item (topic, topic items, and kwargs). """
        self.__contentMeth = dict(
            D = self.__printTopicDescription,
            A = self.__printTopicArgsAll,
            a = self.__printTopicArgNames,
            L = self.__printTopicListeners)
        assert self.allowedExtras == set(self.__contentMeth.keys())
        import sys
        self.__destination = fileObj or sys.stdout
        self.__output = []

        self.__content = extra or ''
        unknownSel = set(self.__content) - self.allowedExtras
        if unknownSel:
            msg = 'These extra chars not known: %s' % ','.join(unknownSel)
            raise ValueError(msg)

        self.__width   = width
        self.__wrapper = TextWrapper(width)
        self.__indent  = 0
        self.__indentStep = indentStep
        self.__topicsBullet     = bulletTopic
        self.__topicItemsBullet = bulletTopicItem
        self.__topicArgsBullet  = bulletTopicArg

    def getOutput(self):
        return '\n'.join( self.__output )

    def _doneTraversal(self):
        if self.__destination is not None:
            self.__destination.write(self.getOutput())

    def _onTopic(self, topicObj):
        """This gets called for each topic. Print as per specified content."""

        # topic name
        self.__wrapper.width = self.__width
        indent = self.__indent
        if topicObj.isAll():
            topicName = self.ALL_TOPICS_NAME
        else:
            topicName = topicObj.getNodeName()
        head = '%s Topic "%s"' % (self.__topicsBullet, topicName)
        self.__output.append( self.__formatDefn(indent, head) )
        indent += self.__indentStep

        # each extra content (assume constructor verified that chars are valid)
        for item in self.__content:
            function = self.__contentMeth[item]
            function(indent, topicObj)

    def _startChildren(self):
        """Increase the indent"""
        self.__indent += self.__indentStep

    def _endChildren(self):
        """Decrease the indent"""
        self.__indent -= self.__indentStep

    def __formatDefn(self, indent, item, defn='', sep=': '):
        """Print a definition: a block of text at a certain indent,
        has item name, and an optional definition separated from
        item by sep. """
        if defn:
            prefix = '%s%s%s' % (' '*indent, item, sep)
            self.__wrapper.initial_indent = prefix
            self.__wrapper.subsequent_indent = ' '*(indent+self.__indentStep)
            return self.__wrapper.fill(defn)
        else:
            return '%s%s' % (' '*indent, item)

    def __printTopicDescription(self, indent, topicObj):
        # topic description
        defn = '%s Description' % self.__topicItemsBullet
        self.__output.append(
            self.__formatDefn(indent, defn, topicObj.getDescription()) )

    def __printTopicArgsAll(self, indent, topicObj, desc=True):
        # topic kwargs
        args = topicObj.getArgDescriptions()
        if args:
            #required, optional, complete = topicObj.getArgs()
            headName = 'Names of Message arguments:'
            if desc:
                headName = 'Descriptions of message arguments:'
            head = '%s %s' % (self.__topicItemsBullet, headName)
            self.__output.append( self.__formatDefn(indent, head) )
            tmpIndent = indent + self.__indentStep
            required = topicObj.getArgs()[0]
            for key, arg in args.items(): # iter in 3, list in 2 ok
                if not desc:
                    arg = ''
                elif key in required:
                    arg = '(required) %s' % arg
                msg = '%s %s' % (self.__topicArgsBullet,key)
                self.__output.append( self.__formatDefn(tmpIndent, msg, arg) )

    def __printTopicArgNames(self, indent, topicObj):
        self.__printTopicArgsAll(indent, topicObj, False)

    def __printTopicListeners(self, indent, topicObj):
        if topicObj.hasListeners():
            item = '%s Listeners:' % self.__topicItemsBullet
            self.__output.append( self.__formatDefn(indent, item) )
            tmpIndent = indent + self.__indentStep
            for listener in topicObj.getListenersIter():
                item = '%s %s (from %s)' % (self.__topicArgsBullet, listener.name(), listener.module())
                self.__output.append( self.__formatDefn(tmpIndent, item) )


def printTreeDocs(rootTopic=None, topicMgr=None, **kwargs):
    """Print out the topic tree to a file (or file-like object like a
    StringIO), starting at rootTopic. If root topic should be root of
    whole tree, get it from pub.getDefaultTopicTreeRoot().
    The treeVisitor is an instance of pub.TopicTreeTraverser.

    Printing the tree docs would normally involve this::

        from pubsub import pub
        from pubsub.utils.topictreeprinter import TopicTreePrinter
        traverser = pub.TopicTreeTraverser( TopicTreePrinter(**kwargs) )
        traverser.traverse( pub.getDefaultTopicTreeRoot() )

    With printTreeDocs, it looks like this::

        from pubsub import pub
        from pubsub.utils import printTreeDocs
        printTreeDocs()

    The kwargs are the same as for TopicTreePrinter constructor:
    extra(None), width(70), indentStep(4), bulletTopic, bulletTopicItem,
    bulletTopicArg, fileObj(stdout). If fileObj not given, stdout is used."""
    if rootTopic is None:
        if topicMgr is None:
            from .. import pub
            topicMgr = pub.getDefaultTopicMgr()
        rootTopic = topicMgr.getRootAllTopics()

    printer = TopicTreePrinter(**kwargs)
    traverser = TopicTreeTraverser(printer)
    traverser.traverse(rootTopic)



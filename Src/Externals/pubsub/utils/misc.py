# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Externals/pubsub/utils/misc.py
# @brief     Implements module/class/test misc
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

"""
Provides useful functions and classes. Most useful are probably
printTreeDocs and printTreeSpec.

:copyright: Copyright since 2006 by Oliver Schoenborn, all rights reserved.
:license: BSD, see LICENSE_BSD_Simple.txt for details.
"""

import sys
from .. import py2and3

__all__ = ('printImported', 'StructMsg', 'Callback', 'Enum' )


def printImported():
    """Output a list of pubsub modules imported so far"""
    ll = [mod for mod in sys.modules.keys() if mod.find('pubsub') >= 0] # iter keys ok
    ll.sort()
    py2and3.print_('\n'.join(ll))


class StructMsg:
    """
    This *can* be used to package message data. Each of the keyword
    args given at construction will be stored as a member of the 'data'
    member of instance. E.g. "m=Message2(a=1, b='b')" would succeed
    "assert m.data.a==1" and "assert m.data.b=='b'". However, use of
    Message2 makes your messaging code less documented and harder to
    debug.
    """

    def __init__(self, **kwargs):
        class Data: pass
        self.data = Data()
        self.data.__dict__.update(kwargs)


class Callback:
    """This can be used to wrap functions that are referenced by class
    data if the data should be called as a function. E.g. given
    >>> def func(): pass
    >>> class A:
    ....def __init__(self): self.a = func
    then doing
    >>> boo=A(); boo.a()
    will fail since Python will try to call a() as a method of boo,
    whereas a() is a free function. But if you have instead
    "self.a = Callback(func)", then "boo.a()" works as expected.
    """
    def __init__(self, callable_):
        self.__callable = callable_
    def __call__(self, *args, **kwargs):
        return self.__callable(*args, **kwargs)


class Enum:
    """Used only internally. Represent one value out of an enumeration
    set.  It is meant to be used as::

        class YourAllowedValues:
            enum1 = Enum()
            # or:
            enum2 = Enum(value)
            # or:
            enum3 = Enum(value, 'descriptionLine1')
            # or:
            enum3 = Enum(None, 'descriptionLine1', 'descriptionLine2', ...)

        val = YourAllowedValues.enum1
        ...
        if val is YourAllowedValues.enum1:
            ...
    """
    nextValue = 0
    values = set()

    def __init__(self, value=None, *desc):
        """Use value if given, otherwise use next integer."""
        self.desc = '\n'.join(desc)
        if value is None:
            assert Enum.nextValue not in Enum.values
            self.value = Enum.nextValue
            Enum.values.add(self.value)

            Enum.nextValue += 1
            # check that we haven't run out of integers!
            if Enum.nextValue == 0:
                raise RuntimeError('Ran out of enumeration values?')

        else:
            try:
                value + Enum.nextValue
                raise ValueError('Not allowed to assign integer to enumerations')
            except TypeError:
                pass
            self.value = value
            if self.value not in Enum.values:
                Enum.values.add(self.value)



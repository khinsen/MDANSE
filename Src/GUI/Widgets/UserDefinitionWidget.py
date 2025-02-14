# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/UserDefinitionWidget.py
# @brief     Implements module/class/test UserDefinitionWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import abc
import os

import wx
import wx.aui as wxaui

from MDANSE import LOGGER, REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Widgets.IWidget import IWidget

class UserDefinitionDialog(wx.Dialog):
    
    def __init__(self,parent,trajectory,udType,*args,**kwargs):

        wx.Dialog.__init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        
        self._mgr = wxaui.AuiManager(self)

        self.datakey = trajectory.filename
         
        self._plugin = REGISTRY['plugin'][udType](self,*args,**kwargs)
        
        self.SetTitle(self._plugin.label)
        
        self.SetSize(self._plugin.GetSize())
        
        self._plugin.set_trajectory(trajectory)
                
        PUBLISHER.sendMessage("msg_set_data", message=self._plugin)
        
    @property
    def plugin(self):
        
        return self._plugin

class UserDefinitionWidget(IWidget):
    
    __metaclass__ = abc.ABCMeta
                    
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._availableUDs = wx.Choice(self._widgetPanel, wx.ID_ANY,style=wx.CB_SORT)
        viewUD = wx.Button(self._widgetPanel, wx.ID_ANY, label="View selected definition")
        newUD = wx.Button(self._widgetPanel, wx.ID_ANY, label="New definition")
        sizer.Add(self._availableUDs, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(viewUD, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(newUD, 0, wx.ALL|wx.EXPAND, 5)

        PUBLISHER.subscribe(self.msg_set_ud, "msg_set_ud")

        self.Bind(wx.EVT_BUTTON, self.on_view_definition, viewUD)
        self.Bind(wx.EVT_BUTTON, self.on_new_definition, newUD)

        return sizer

    def OnDestroy(self,event):
        
        PUBLISHER.unsubscribe(self.msg_set_ud, 'msg_set_ud')
        IWidget.OnDestroy(self,event)
        
    def on_view_definition(self,event):
        
        viewUD = event.GetEventObject()
        ud = viewUD.Parent.GetChildren()[0].GetStringSelection()       
        if not ud:
            LOGGER("Please select a user definition","error",["dialog"])
            return
        
        from MDANSE.GUI.UserDefinitionViewer import UserDefinitionViewer
        
        f = UserDefinitionViewer(self,ud=[self._basename,self._type,ud])
        
        f.Show()
    
    def on_new_definition(self,event):
        
        dlg = UserDefinitionDialog(None,self._trajectory,self._type)
        
        dlg.ShowModal()
        
    def get_widget_value(self):
        
        return str(self._availableUDs.GetStringSelection())    

    def set_data(self, datakey):

        self._filename = datakey

        self._trajectory = DATA_CONTROLLER[datakey]

        self._basename = os.path.basename(self._filename)
        
        self.msg_set_ud(None)

    def msg_set_ud(self,message):
         
        uds = UD_STORE.filter(self._basename, self._type)

        currentSelection = self._availableUDs.GetStringSelection()
        
        self._availableUDs.SetItems(uds)
        
        if currentSelection:
            self._availableUDs.SetStringSelection(currentSelection)

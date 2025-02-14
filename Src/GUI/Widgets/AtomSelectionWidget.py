# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/AtomSelectionWidget.py
# @brief     Implements module/class/test AtomSelectionWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

import wx

from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.Widgets.UserDefinitionWidget import UserDefinitionDialog, UserDefinitionWidget
from MDANSE.GUI.Icons import ICONS

class AtomSelectionWidget(UserDefinitionWidget):
         
    def add_widgets(self):
 
        self._sizer = wx.BoxSizer(wx.VERTICAL)

        panel = wx.Panel(self._widgetPanel,wx.ID_ANY)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        new = wx.Button(panel, wx.ID_ANY, label="Set new selection")
        new.SetToolTip(wx.ToolTip("Pop up selection dialog"))
        add = wx.BitmapButton(panel, wx.ID_ANY, ICONS["plus",16,16])
        add.SetToolTip(wx.ToolTip("Add a new line"))

        sizer.Add(new, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
        sizer.Add(add, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
        
        panel.SetSizer(sizer)
        
        self._sizer.Add(panel, 1, wx.ALL|wx.ALIGN_RIGHT, 5)
        
        self._choices = []

        PUBLISHER.subscribe(self.msg_set_ud, "msg_set_ud")

        self.Bind(wx.EVT_BUTTON, self.on_new_definition, new)
        self.Bind(wx.EVT_BUTTON, self.on_add_definition, add)
        
        return self._sizer
          
    def on_add_definition(self,event):
        
        panel = wx.Panel(self._widgetPanel,wx.ID_ANY)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        availableUDs = wx.Choice(panel, wx.ID_ANY,style=wx.CB_SORT)
        uds = UD_STORE.filter(self._basename, "atom_selection")
        availableUDs.SetItems(uds)
        
        view = wx.Button(panel, wx.ID_ANY, label="View selected definition")
        remove = wx.BitmapButton(panel, wx.ID_ANY, ICONS["minus",16,16])

        sizer.Add(availableUDs, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(view, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(remove, 0, wx.ALL|wx.EXPAND, 5)
        
        panel.SetSizer(sizer)
        
        self._sizer.Add(panel,1,wx.ALL|wx.EXPAND,5)
        
        self._widgetPanel.GrandParent.Layout()
        self._widgetPanel.GrandParent.Refresh()

        self.Bind(wx.EVT_BUTTON, self.on_view_definition, view)
        self.Bind(wx.EVT_BUTTON, self.on_remove_definition, remove)

    def on_new_definition(self,event):
        
        dlg = UserDefinitionDialog(None,self._trajectory,'atom_selection')
        
        dlg.ShowModal()

    def on_remove_definition(self,event):
        
        self._sizer.Detach(event.GetEventObject().Parent)
        
        event.GetEventObject().Parent.Destroy()

        self._widgetPanel.GrandParent.Layout()

    def get_widget_value(self):

        sizerItemList = list(self._sizer.GetChildren())
        del sizerItemList[0]

        uds = []
        for sizerItem in sizerItemList:
            
            panel = sizerItem.GetWindow()
            children = panel.GetChildren()
            udName = children[0]            
            uds.append(udName.GetStringSelection())
                  
        if not uds:
            return None
        else:
            return uds

    def msg_set_ud(self,message):
         
        uds = UD_STORE.filter(self._basename, self._type)
        
        sizerItemList = list(self._sizer.GetChildren())
        del sizerItemList[0]

        for sizerItem in sizerItemList:
            
            panel = sizerItem.GetWindow()
            children = panel.GetChildren()
            udName = children[0]
            oldSelection = udName.GetStringSelection()            
            udName.SetItems(uds)
            udName.SetStringSelection(oldSelection)
         
REGISTRY["atom_selection"] = AtomSelectionWidget
   
if __name__ == "__main__":
    
    from MMTK.Trajectory import Trajectory
    
    from MDANSE import PLATFORM
    
    t = Trajectory(None,os.path.join(PLATFORM.example_data_directory(),"Trajectories","MMTK","protein_in_periodic_universe.nc"),"r")
    
    app = wx.App(False)
    
    p = UserDefinitionDialog(None,t,'q_vectors')
        
    p.SetSize((800,800))
            
    p.ShowModal()
    
    app.MainLoop()
        

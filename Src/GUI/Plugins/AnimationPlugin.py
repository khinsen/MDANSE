# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/AnimationPlugin.py
# @brief     Implements module/class/test AnimationPlugin
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx
import wx.aui as wxaui

from MDANSE import REGISTRY
from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.Icons import ICONS
from MDANSE.GUI.Plugins.ComponentPlugin import ComponentPlugin

class AnimationPlugin(ComponentPlugin):
        
    label = "Animation"
    
    ancestor = ["molecular_viewer"]
        
    def __init__(self, parent, *args, **kwargs):
        
        ComponentPlugin.__init__(self, parent, size=(-1,50), *args, **kwargs)
                    
    def build_panel(self):   
 
        panel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())
 
        controlSizer = wx.BoxSizer(wx.HORIZONTAL)

        firstButton = wx.BitmapButton(panel, wx.ID_ANY, ICONS["first",32,32])
        self.startStop = wx.BitmapButton(panel, wx.ID_ANY, ICONS["play",32,32])
        lastButton = wx.BitmapButton(panel, wx.ID_ANY, ICONS["last",32,32])
        self.frameSlider = wx.Slider(panel,id=wx.ID_ANY, value=0, minValue=0, maxValue=1, style=wx.SL_HORIZONTAL)
        self.frameSlider.SetRange(0,self._parent.n_frames-1)            
        self.frameEntry = wx.TextCtrl(panel,id=wx.ID_ANY,value="0", size=(60,20), style= wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)        
        speedBitmap = wx.StaticBitmap(panel,-1, ICONS["clock",42,42])
        self.speedSlider = wx.Slider(panel,id=wx.ID_ANY,value=0,minValue=0,maxValue=1,style=wx.SL_HORIZONTAL)
        self.speedSlider.SetRange(0,self._parent.max_laps)
        speed = self._parent.max_laps - self._parent.timer_interval
        self.speedSlider.SetValue(speed)
        self.speedEntry = wx.TextCtrl(panel,id=wx.ID_ANY,value=str(speed), size=(60,20), style= wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        controlSizer.Add(firstButton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL,5)
        controlSizer.Add(self.startStop, 0,  wx.ALIGN_CENTER_VERTICAL)
        controlSizer.Add(lastButton, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.Add((5, -1), 0, wx.ALIGN_RIGHT)

        controlSizer.Add(self.frameSlider, 3, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.Add(self.frameEntry, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.Add((5, -1), 0, wx.ALIGN_RIGHT)

        controlSizer.Add(speedBitmap, 0 , wx.ALIGN_CENTER_VERTICAL) 
        controlSizer.Add((5, -1), 0, wx.ALIGN_RIGHT)

        controlSizer.Add(self.speedSlider, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL) 
        controlSizer.Add(self.speedEntry, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL,5) 
                
        panel.SetSizer(controlSizer)
        controlSizer.Fit(panel)        
        panel.Layout()
                
        self._mgr.AddPane(panel, wxaui.AuiPaneInfo().Center().Dock().CaptionVisible(False).CloseButton(False).MinSize(self.GetSize()))

        self._mgr.Update()

        self.Bind(wx.EVT_SCROLL, self.on_frame_sliding, self.frameSlider)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_set_frame, self.frameEntry)
        
        self.Bind(wx.EVT_SLIDER, self.on_change_frame_rate, self.speedSlider)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_set_speed, self.speedEntry)
        
        self.Bind(wx.EVT_BUTTON, self.on_start_stop_animation, self.startStop)
        self.Bind(wx.EVT_BUTTON, self.on_goto_first_frame, firstButton)
        self.Bind(wx.EVT_BUTTON, self.on_goto_last_frame, lastButton)
                
        PUBLISHER.subscribe(self.msg_update_animation_icon, 'msg_animate_trajectory')
        PUBLISHER.subscribe(self.msg_set_trajectory, 'msg_set_trajectory')
        PUBLISHER.subscribe(self.msg_timer, 'msg_timer')
                
    def plug(self):
        self._parent._mgr.GetPane(self).LeftDockable(False).RightDockable(False).Dock().Bottom().CloseButton(True)
        
        self._parent._mgr.Update()        

    def on_change_frame_rate(self, event=None):

        laps = self.speedSlider.GetValue()
        
        self._parent.change_frame_rate(laps)
        
        self.speedEntry.SetValue(str(self.speedSlider.GetValue()))        

    def on_frame_sliding(self, event=None):
        
        frame = self.frameSlider.GetValue()
        
        self._parent.set_frame(frame)
        
        frame = self._parent.current_frame
        
        self.frameEntry.SetValue(str(frame))
        self.frameSlider.SetValue(frame)
        
    def on_goto_first_frame(self, event=None):
        
        self._parent.goto_first_frame()

        self.frameEntry.SetValue(str(0))
        self.frameSlider.SetValue(0)

    def on_goto_last_frame(self, event=None):

        self._parent.goto_last_frame()

        self.frameEntry.SetValue(str(self._parent.n_frames-1))
        self.frameSlider.SetValue(self._parent.n_frames-1)

    def on_set_speed(self, event=None):

        self.speedSlider.SetValue(int(self.speedEntry.GetValue()))        
        self._parent.change_frame_rate()
                
    def msg_timer(self, message):
        
        plugin = message
        if not plugin.is_parent(self):
            return
        
        frame = plugin.current_frame
        
        self.frameEntry.SetValue(str(frame))
        self.frameSlider.SetValue(int(frame))
        
    def on_set_frame(self, event=None):
        
        frame = int(self.frameEntry.GetValue())
        
        self._parent.set_configuration(frame)
        
        self.frameSlider.SetValue(frame)
        
    def on_start_stop_animation(self, event=None):
        
        self._parent.start_stop_animation()

    def msg_update_animation_icon(self, message):
 
        plugin = message
        if not plugin.is_parent(self):
            return
                 
        if plugin.animation_loop:
            self.startStop.SetBitmapLabel(ICONS["pause",32,32])
        else:
            self.startStop.SetBitmapLabel(ICONS["play",32,32])

    def msg_set_trajectory(self, message):
        
        plugin = message
        if not plugin.is_parent(self):
            return
 
        self.frameSlider.SetRange(0,self._parent.n_frames-1)
        
REGISTRY["animation"] = AnimationPlugin
    

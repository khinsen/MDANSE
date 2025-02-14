# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/JobControllerPanel.py
# @brief     Implements module/class/test JobControllerPanel
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import cPickle
import datetime
import glob
import os
import threading
import time

import wx
import wx.lib.intctrl as intctrl

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Singleton import Singleton
from MDANSE.Framework.Status import convert_duration, total_seconds

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.Icons import ICONS
from MDANSE.GUI.Events.JobControllerEvent import EVT_JOB_CONTROLLER, JobControllerEvent
        
class JobController(threading.Thread):
    '''
    This class sets up the job controlling daemon that will regurlarly check for the status of running MDANSE jobs.
    
    The job controller run on a separate thread in order to non-block the main thread.
    
    When the thread is running, it will check every 10s the status of the MDANSE running jobs by looking at their 
    corresponding temporary pickle files. It unpickles them and updates the :py:attr:`_runningJobs` dictionnary used to store
    the information about each running jobs (state, progress, eta, name ...). That dictionnary is passed to the job 
    controller panel widget using wx.PostEvent mechanism. In doing the job controller panel widget just has to bind 
    to EVT_JOB_CONTROLLER and it will receive the updated version of :py:attr:`_runningJobs` dictionnary every time 
    the :py:meth:run is called.     
    '''
    
    __metaclass__ = Singleton
    
    def __init__(self, window, start=False):
        '''
        
        :param window: the wx object that will be notify when job controller is updated
        :type window: wx object
        :param start: if True the job controller thread is started at __init__ stage.
        :type start: bool
        '''
        
        threading.Thread.__init__(self)

        self.setDaemon(True)
        
        # The wx object related to this thread
        self._window = window
        
        self._stop = threading.Event()
                                
        self._runningJobs = collections.OrderedDict()
                
        # This variable is used to keep track whether or not it is the first run of the thread.
        self._firstThreadRun = True
        
        if start:
            self.start()
        
    @property
    def runningJobs(self):
        
        return self._runningJobs

    def kill_job(self, info):
                
        if self._runningJobs.has_key(info["name"]):

            if info['state'] == 'running':
                try:
                    PLATFORM.kill_process(info['pid'])
                except:
                    pass

            del self._runningJobs[info["name"]]

        if os.path.exists(info['temporary_file']):            
            try:
                os.unlink(info['temporary_file'])
            except:
                pass

        self.update()
        
    def run(self):
        
        while not self._stop.is_set():
            self.update()
            self._stop.wait(10.0)

    def stop(self):
        
        self._stop.set()
        
    def update(self, init=False):
                
        pids = PLATFORM.get_processes_info()
                        
        # The list of the registered jobs.
        jobs = [f for f in glob.glob(os.path.join(PLATFORM.temporary_files_directory(),'*'))]
                        
        # Loop over the job registered at the previous controller check point     
        for job in self._runningJobs.keys():            

            # Case where a job has finished during two controller check points (i.e. its temporary file has been deleted)
            if self._runningJobs[job]['state'] == 'finished':
                continue
            
            # Case where the jobs has finished properly (e.g. its temporary file has been removed)
            if not job in jobs:
                self._runningJobs[job]['eta'] = 'N/A'
                self._runningJobs[job]['progress'] = 100
                self._runningJobs[job]['state'] = 'finished'
                start = datetime.datetime.strptime(self._runningJobs[job]["start"],"%d-%m-%Y %H:%M:%S")
                self._runningJobs[job]['elapsed'] = '%02d:%02dh:%02dm:%02ds' % convert_duration(total_seconds(datetime.datetime.today() - start))
                
        # Loop over the job whose temporary files are still present
        for job in jobs:

            # Open the job temporary file
            try:
                f = open(job, 'rb')
                info = cPickle.load(f)
                f.close()
                
            # If the file could not be opened/unpickled for whatever reason, try at the next checkpoint
            except:
                continue

            # The job file could be opened and unpickled properly
            else:
                
                name = info['name']
                                
                # Check that the pid of the running job corresponds to an active pid.
                running = (info['pid'] in pids)
                
                # If so, check that the corresponding pid actually corresponds to the job by comparing 
                # the job starting date and the pid creation date.
                if running:
                    jobStartingTime = datetime.datetime.strptime(info["start"],"%d-%m-%Y %H:%M:%S")
                    procStartingTime = datetime.datetime.strptime(pids[info['pid']],"%d-%m-%Y %H:%M:%S")
                    running = (jobStartingTime >= procStartingTime)
                    
                if not running:
                    info["state"] = "aborted"
                    
                # If the job was aborted, display the traceback on the dialog logger and remove the corresponding job temporary file
                if self._firstThreadRun and info['state'] == 'aborted':
                    self.kill_job(info)
                    continue

                self._runningJobs[name] = info
                
        wx.PostEvent(self._window, JobControllerEvent(self._runningJobs))
        
        self._firstThreadRun = False

                                              
class JobControllerPanel(wx.ScrolledWindow):
    
    columns = [("name",(180,-1)),("pid",(60,-1)),("start",(150,-1)),("elapsed",(140,-1)),("state",(90,-1)),("progress",(-1,-1)),("eta",(120,-1)),("kill",(50,-1))]
    
    def __init__(self, parent):
        
        wx.ScrolledWindow.__init__(self, parent, id = wx.ID_ANY)

        self.SetScrollbars(pixelsPerUnitX=1, pixelsPerUnitY=1, noUnitsX=50, noUnitsY=50)
        
        self.parent = parent
                                
        self._gbSizer = wx.GridBagSizer(0,0)

        for i,(col,s) in enumerate(JobControllerPanel.columns):
            self._gbSizer.Add(wx.TextCtrl(self,wx.ID_ANY,value=col.upper(),size=s,style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL),pos=(0,i),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)

        self._gbSizer.AddGrowableCol(5)
                        
        self.SetSizer(self._gbSizer)

        self._jobsController = JobController(self,True)
        
        self._jobs = {}

        EVT_JOB_CONTROLLER(self,self.on_update)
        
        self.Bind(wx.EVT_WINDOW_DESTROY,self.OnDestroy)
        
        PUBLISHER.subscribe(self.msg_start_job,"msg_start_job")

    def __del__(self):

        self._jobsController.stop()
        while self._jobsController.is_alive():
            time.sleep(0.01)
            
    def OnDestroy(self,event):
        
        PUBLISHER.subscribe(self.msg_start_job,"msg_start_job")
        event.Skip()
        
    def msg_start_job(self,message):
        t = threading.Thread(target=self.updateJobsController)
        t.start()

    def updateJobsController(self):
        time.sleep(PLATFORM.jobs_launch_delay())
        self._jobsController.update()

    def on_display_info(self,event):
        
        row = self._gbSizer.GetItemPosition(event.GetEventObject())[0]
        name = self._gbSizer.FindItemAtPosition((row,0)).Window.GetLabel() 

        f = wx.Frame(self,size=(800,500))
                
        panel = wx.Panel(f,wx.ID_ANY)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        info = self._jobsController.runningJobs[name]['info'].strip()
        if not info:
            info = "No information available about %r job." % name
        
        self._info = wx.TextCtrl(panel,wx.ID_ANY,style=wx.TE_AUTO_SCROLL|wx.TE_READONLY|wx.TE_MULTILINE)
        self._info.SetValue(info)
        
        sizer.Add(self._info,1,wx.ALL|wx.EXPAND,5)
        
        panel.SetSizer(sizer)
        
        f.Show()

    def on_display_traceback(self,event):
        
        row = self._gbSizer.GetItemPosition(event.GetEventObject())[0]
        name = self._gbSizer.FindItemAtPosition((row,0)).Window.GetLabel() 

        f = wx.Frame(self,size=(800,500))
                
        panel = wx.Panel(f,wx.ID_ANY)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        tb = self._jobsController.runningJobs[name]['traceback'].strip()
        if not tb:
            tb = "No traceback available about %r job." % name
        
        self._tb = wx.TextCtrl(panel,wx.ID_ANY,style=wx.TE_AUTO_SCROLL|wx.TE_READONLY|wx.TE_MULTILINE)
        self._tb.SetValue(tb)
        
        sizer.Add(self._tb,1,wx.ALL|wx.EXPAND,5)
        
        panel.SetSizer(sizer)
        
        f.Show()
                                    
    def on_kill_job(self, event):
                
        row = self._gbSizer.GetItemPosition(event.GetEventObject())[0]
        name = self._gbSizer.FindItemAtPosition((row,0)).Window.GetLabel() 

        d = wx.MessageDialog(None, 'Do you really want to kill job %r ?' % name, 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_EXCLAMATION)
        if d.ShowModal() == wx.ID_YES:
            self._jobsController.kill_job(self._jobsController.runningJobs[name])
                        
    def on_update(self, event):
                                        
        runningJobs = event.runningJobs

        # Remove the widgets corresponding to the jobs that are not running anymore  
        for k,v in self._jobs.items():

            if runningJobs.has_key(k):
                continue
                                    
            row,_ = self._gbSizer.GetItemPosition(v['name'])            
            for c in range(self._gbSizer.GetCols()):
                w = self._gbSizer.FindItemAtPosition((row,c))
                w.GetWindow().Destroy()
            del self._jobs[k]
        
            for r in range(row+1,self._gbSizer.GetRows()):
                for i in range(self._gbSizer.GetCols()):
                    w = self._gbSizer.FindItemAtPosition((r,i))
                    if w is None:
                        continue
                    self._gbSizer.SetItemPosition(w.GetWindow(),(r-1,i))

        for jobName, jobStatus in runningJobs.items():
                        
            if self._jobs.has_key(jobName):
                self._jobs[jobName]['progress'].SetValue(jobStatus['progress'])
                self._jobs[jobName]['elapsed'].SetValue(jobStatus['elapsed'])
                self._jobs[jobName]['state'].SetLabel(jobStatus['state'])
                self._jobs[jobName]['eta'].SetValue(jobStatus['eta'])
            else:
                self._jobs[jobName] = {}
                self._jobs[jobName]['name'] = wx.Button(self, wx.ID_ANY, style=wx.BU_EXACTFIT,label=jobStatus['name'])
                self._jobs[jobName]['pid'] = intctrl.IntCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL,value=jobStatus['pid'])
                self._jobs[jobName]['start'] = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL,value=jobStatus['start'])
                self._jobs[jobName]['elapsed'] = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL,value=jobStatus['elapsed'])
                self._jobs[jobName]['state'] = wx.Button(self, wx.ID_ANY, style=wx.BU_EXACTFIT,label=jobStatus['state'])
                self._jobs[jobName]['progress'] = wx.Gauge(self, wx.ID_ANY,range=100)
                self._jobs[jobName]['progress'].SetValue(jobStatus['progress'])
                self._jobs[jobName]['eta'] = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_READONLY|wx.ALIGN_CENTER_HORIZONTAL,value=jobStatus['eta'])
                self._jobs[jobName]['kill'] = wx.BitmapButton(self, wx.ID_ANY, ICONS["stop",16,16])

                r = len(self._jobs)
                        
                self._gbSizer.Add(self._jobs[jobName]['name']    ,pos=(r,0),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
                self._gbSizer.Add(self._jobs[jobName]['pid']     ,pos=(r,1),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
                self._gbSizer.Add(self._jobs[jobName]['start']   ,pos=(r,2),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
                self._gbSizer.Add(self._jobs[jobName]['elapsed'] ,pos=(r,3),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
                self._gbSizer.Add(self._jobs[jobName]['state']   ,pos=(r,4),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
                self._gbSizer.Add(self._jobs[jobName]['progress'],pos=(r,5),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
                self._gbSizer.Add(self._jobs[jobName]['eta']     ,pos=(r,6),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
                self._gbSizer.Add(self._jobs[jobName]['kill']    ,pos=(r,7),flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)

            if jobStatus["state"] == "aborted":
                self._jobs[jobName]["name"].SetBackgroundColour(wx.RED)
                
            self.Bind(wx.EVT_BUTTON,self.on_display_info,self._jobs[jobName]['name'])
            self.Bind(wx.EVT_BUTTON,self.on_display_traceback,self._jobs[jobName]['state'])
            self.Bind(wx.EVT_BUTTON, self.on_kill_job,self._jobs[jobName]['kill'])

        self._gbSizer.Layout()
                                                                                                    
if __name__ == "__main__":
        
    app = wx.App(0)
    frame = wx.Frame(None, -1, "Job Controller")
     
    JobController = JobControllerPanel(frame)
     
    frame.Show(True)
    app.MainLoop()
    
    
    
    

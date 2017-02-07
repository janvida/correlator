#!/usr/bin/python
#CorrelatorGUI.py

import sys
import os
import time
import wx
import wx.lib.plot as plot
import thread
import serial

class PlotWin(wx.Frame):
    ''' Plot window for waveform capture and integration'''
    def __init__(self, title):
        wx.Frame.__init__(self, None, wx.ID_ANY, title)
        self.plot = plot.PlotCanvas(self)
        self.plot.SetInitialSize(size=(300,200))
        self.plot.SetEnableZoom(True)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    def PlotTrace(self, traceA, traceB):
        '''Plot ADC waveforms'''
        plts = []
        if traceA:
            plts.append(plot.PolyLine(traceA, colour='blue', width=1))
        if traceB:
            plts.append(plot.PolyLine(traceB, colour='red', width=1))
        self.plot.SetUseScientificNotation(False)
        gc = plot.PlotGraphics(plts, 'ADC Waveform Data', 'uS', 'ADC')
        self.plot.Draw(gc)
        self.Show(True)
    def PlotAccum(self, accum):
        '''Plot Correlation Integral'''
        plts = [plot.PolyLine(accum, colour='black', width=1)]
        self.plot.SetUseScientificNotation(True)
        gc = plot.PlotGraphics(plts, 'Correlation Integral', 'sec', 'integral')
        self.plot.Draw(gc)
        self.Show(True)
    def OnClose(self, event):
        '''Hide the window, don't close'''
        self.Show(False) # hide window
        event.Veto()

class CorrelatorWin(wx.Frame):
    '''Main IIF Corrilator application window'''
    ACCUM_STOP, ACCUM_START, ACCUM_ACTIVE = range(3)
    def __init__(self, title, app, rec):
        wx.Frame.__init__(self, None, wx.ID_ANY, title, size=(390,380),
            style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)
        self.app = app
        # Create a status bar at the bottom of the window
        self.CreateStatusBar()
        # Create a menu bar
        menuBar = wx.MenuBar()
        # Create menu options
        fileMenu = wx.Menu()
        helpMenu = wx.Menu()
        # Create menu items and add them to the menu options
        self.record_label = ('Enable Recording\tCtrl-R','Disable Recording\tCtrl-R')
        self.record_enable = rec
        self.record_menu = fileMenu.Append(wx.ID_ANY, self.record_label[rec],
            'Enable/disable data recoding')
        self.record_path = ''
        # create record file
        self.tmp_name = '/tmp/correlator%d.dat' % os.getpid()
        self.tmp_file = open(self.tmp_name, 'w')

        menuClear = fileMenu.Append(wx.ID_ANY, 'Clear Record\tCtrl-C',
            'Clear record buffer')
        menuSave =fileMenu.Append(wx.ID_ANY, 'Save Record...\tCtrl-S',
            'Save record to file')
        menuExit = fileMenu.Append(wx.ID_EXIT, 'E&xit...', 'Terminate program')
        menuHelp = helpMenu.Append(wx.ID_HELP, '&Help')
        menuAbout = helpMenu.Append(wx.ID_ABOUT, '&About',
            'Information about this program')
        # Add menu options to the menu bar
        menuBar.Append(fileMenu,'&File')
        menuBar.Append(helpMenu,'&Help')
        # Show menu bar
        self.SetMenuBar(menuBar)
        # Bind menu events 
        self.Bind(wx.EVT_MENU, self.OnRecord, self.record_menu)
        self.Bind(wx.EVT_MENU, self.OnClear, menuClear)
        self.Bind(wx.EVT_MENU, self.OnSave, menuSave)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        # Layout widgits
        panel = wx.Panel(self, -1)
        app.IifCmd('iiec0') # don't echo characters
        # LEDs section
        wx.StaticBox(panel, -1, 'LEDs', (5,5), (380,40))
        self.led = []
        for n in range(8):
             cb = wx.CheckBox(panel, -1, str(n), (335-45*n,20), style=wx.ALIGN_RIGHT)
             self.led.append(cb)
             wx.EVT_CHECKBOX(self, cb.GetId(), self.OnLED)
        app.IifCmd('iild') # query current LED states
        # Channel Gain and Phase period sections
        self.gain = [None, None]
        self.period = [None, None]
        for ch in range(2):
            chan = 'ab'[ch]
            wx.StaticBox(panel, -1, 'Channel %c' % chan.upper(), (5+195*ch,50), (185,90))
            wx.StaticText(panel, -1, 'Gain:', (15+195*ch,75))
            sp = wx.SpinCtrl(panel, -1, '0', (80+195*ch,70), max=15)
            sp.chan = ch
            self.Bind(wx.EVT_SPINCTRL, self.OnGain, sp)
            self.gain[ch] = sp
            app.IifCmd('iig' + chan) # query current gain settings
            wx.StaticText(panel, -1, 'Period:', (15+195*ch,110))
            sp = wx.SpinCtrl(panel, -1, '0', (80+195*ch,105), max=65535)
            sp.chan = ch
            self.Bind(wx.EVT_SPINCTRL, self.OnPerd, sp)
            self.period[ch] = sp
            app.IifCmd('iip' + chan) # query current phase period settings
        # Channel A-B delay section
        wx.StaticBox(panel, -1, 'Delay', (5,145), (380,50))
        wx.StaticText(panel, -1, 'Channel B-A:', (100,165))
        self.delay = wx.SpinCtrl(panel, -1, '0', (200, 160), min=-5120, max=5119)
        app.IifCmd('iida', 'iidb0', 'iidc') # query fine, course delay settings
        self.Bind(wx.EVT_SPINCTRL, self.OnDelay, self.delay)
        # Integrate section
        self.intTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnIntPeriod, self.intTimer)
        wx.StaticBox(panel, -1, 'Integrate', (5,200), (185,125))
        wx.StaticText(panel, -1, 'Duration:', (15,225))
        wx.StaticText(panel, -1, 'Period:', (15,260))
        self.intDuration = wx.SpinCtrl(panel, -1, '0', (80,220), max=86400)
        self.intPeriod = wx.SpinCtrl(panel, -1, '1', (80,255), min=0, max=3600)
        self.intStart = wx.Button(panel, -1, 'Start', (45,290),(100,-1))
        self.Bind(wx.EVT_BUTTON, self.OnIntegrate, self.intStart)
        self.accumulating = False
        self.accumulator = 0
        # Capture section
        wx.StaticBox(panel, -1, 'Capture', (200,200), (185,125))
        wx.StaticText(panel, -1, 'Length:', (205, 260))
        self.capa = wx.CheckBox(panel, -1, 'A', (235,225), style=wx.ALIGN_RIGHT)
        self.capa.SetValue(True)
        self.capa.SetForegroundColour('red')
        wx.EVT_CHECKBOX(self, self.capa.GetId(), self.OnCapChan)
        self.capb = wx.CheckBox(panel, -1, 'B', (305,225), style=wx.ALIGN_RIGHT)
        self.capb.SetValue(True)
        self.capb.SetForegroundColour('blue')
        wx.EVT_CHECKBOX(self, self.capb.GetId(), self.OnCapChan)
        self.capLength = wx.SpinCtrl(panel, -1, '20480', (275,255), min=1, max=20480)
        self.plot = wx.Button(panel, -1, 'Plot', (240,290),(100,-1))
        self.Bind(wx.EVT_BUTTON, self.OnCapture, self.plot)
    # Callback functions
    def OnClose(self, event):
        '''Verify closing application'''
        self.SetStatusText('exit?')
        message = wx.MessageDialog(None, 'Are you sure you want to quit?',
             'Confirm exit',wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if message.ShowModal() == wx.ID_YES:
            self.app.plt.Destroy()
            self.Destroy()
        else:
            event.Veto()
    def OnExit(self, event):
        self.app.plt.Destroy()
        self.Destroy()
    def OnRecord(self, event):
        self.record_enable = not self.record_enable
        label = self.record_label[self.record_enable]
        self.GetMenuBar().SetLabel(self.record_menu.GetId(), label)
        self.SetStatusText('Recording ' + ['Disabled','Enabled'][self.record_enable])
    def OnClear(self, event):
        self.tmp_file.seek(0)
        self.tmp_file.truncate(0)
        self.SetStatusText('Record cleared')
    def OnSave(self, event):
        wildcard = "Data files (*.dat)|*.dat|All files (*.*)|*.*"
        dialog = wx.FileDialog(self, 'Save data record', '', self.record_path,
            wildcard, wx.SAVE | wx.CHANGE_DIR | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            self.record_path = dialog.GetPath()
            try:
                self.tmp_file.close()
                os.rename(self.tmp_name, self.record_path)
                self.tmp_file = open(self.tmp_name, 'w')
                self.SetStatusText('Record saved to: ' + self.record_path)
            except:
                self.SetStatusText('Failed to open: ' + self.record_path)
        else:
            self.SetStatusText('Record not saved')
    def OnLED(self, event):
        '''Update LEDs on IIF'''
        led = 0
        for n in range(8):
            if self.led[n].IsChecked():
                led |= (1 << n)     
        self.app.IifCmd('iild%02x' % led);
        self.SetStatusText('Setting LEDs to %02X' % led)
    def OnGain(self, event):
        '''Update channel gain on IIF'''
        ch = event.GetEventObject().chan
        chan = 'ab'[ch]
        val = self.gain[ch].GetValue()
        self.app.IifCmd('iig%c%x' % (chan, val))
        self.SetStatusText('Setting %c gain to %X' % (chan.upper(), val))
    def OnPerd(self, event):
        '''Update channel phase period on IIF'''
        ch = event.GetEventObject().chan
        chan = 'ab'[ch]
        val = self.period[ch].GetValue()
        self.app.IifCmd('iip%c%04x' % (chan, val))
        self.SetStatusText('Setting %c phase period to %04X' % (chan.upper(), val))
    def OnDelay(self, event):
        '''Update channel B-A delay on IIF'''
        val = 5120 + self.delay.GetValue()
        da, dc = val % 5, val // 5
        self.app.IifCmd('iida%x' % da, 'iidc%03x' % dc)
        self.SetStatusText('Setting B-A delay to %dnS' % (val - 5120))
    def OnCapChan(self, event):
        '''make sure we capture at least one channel'''
        this_chan = event.GetEventObject()
        if not this_chan.IsChecked():
            other_chan = self.capb if this_chan is self.capa else self.capa
            if not other_chan.GetValue():
                other_chan.SetValue(True)
    def OnIntegrate(self, event):
        '''Start/Stop correlator integration'''
        if self.accumulating == self.ACCUM_STOP:
            self.intStart.SetLabel('Stop')
            self.accumulating = self.ACCUM_START
            self.int_period = self.intPeriod.GetValue()
            self.app.IifCmd('iiac') # prime the pump
        else:
            self.intStart.SetLabel('Start')
            self.accumulating = self.ACCUM_STOP
    def OnIntPeriod(self, event):
        self.app.IifCmd('iiac')
    def OnCapture(self, event):
        '''Capture channel trace data'''
        self.app.IifCmd('iicp')
        self.capture_max = (self.capLength.GetValue() + 75) // 80
    def OnIif(self, msg):
        '''Handle IIF messages'''
        if self.record_enable:
            self.tmp_file.write(msg + '\n')
        if self.app.IifAck(msg):
            # message is a command acknowledge
            if msg.startswith('IILD'):
                val = int(msg[4:], 16)
                update = False
                for n in range(8):
                    bit = 0 != (val & (1 << n))
                    if bit != self.led[n].IsChecked():
                        self.led[n].SetValue(bit)
                        update = True
                if update:
                    self.SetStatusText('Updating LED states to %02X' % val)
            elif msg.startswith('IIG'):
                chan = msg[3]
                val = int(msg[4:], 16)
                ch = 1 if chan == 'B' else 0
                if val != self.gain[ch].GetValue():
                    self.gain[ch].SetValue(val)
                    self.SetStatusText('Updating channel %c gain to %X' % (chan, val))
            elif msg.startswith('IIP'):
                chan = msg[3]
                val = int(msg[4:], 16)
                ch = 1 if chan == 'B' else 0
                if val != self.period[ch].GetValue():
                    self.period[ch].SetValue(val)
                    self.SetStatusText('Updating channel %c phase-period to %04X' % (chan, val))
            elif msg.startswith('IID'):
                chan = msg[3]
                val = int(msg[4:], 16)
                if chan == 'A':
                    self.delay_da = val;
                elif chan == 'B':
                    pass # initialized and assumed to be zero
                else:
                    val = (5 * val) + self.delay_da - 5120
                    if val != self.delay.GetValue():
                        self.delay.SetValue(val)
                        self.SetStatusText('Updating channel B-A delay to %dnS' % val)
            elif msg.startswith('IIAC'):
                if self.accumulating == self.ACCUM_START:
                    self.app.ClrAccum()
                    self.accumulator = 0
                    self.SetStatusText('Integrator:')
            elif msg.startswith('IIAR'):
                val = int(msg[4:], 16)
                if val >= (1<<63): val -= (1<<64)
                self.accumulator += val
                self.app.PlotAccum(self.accumulator)
                dt = self.integrate_stop_time - time.time() # time left
                if self.accumulating == self.ACCUM_ACTIVE and dt > 0:
                    if not self.int_period: self.app.IifCmd('iiac')
                    self.SetStatusText('Integrator: %d [%d]' % (self.accumulator, dt))
                else:
                    self.intTimer.Stop()
                    if self.accumulating != self.ACCUM_STOP:
                        self.intStart.SetLabel('Start')
                        self.accumulating = self.ACCUM_STOP
                    self.SetStatusText('Integrator: %d' % self.accumulator)
            elif msg.startswith('IICP'):
                self.app.ClrTrace()
                self.capture_page = 0
                if self.capa.IsChecked():
                    self.app.IifCmd('iica00')
                else:
                    self.app.IifCmd('iicb00')
                self.SetStatusText('Reading ADC waveform data...')
                self.plot.Enable(False) # disable button until done
            elif msg.startswith('IIC'):
                chan = msg[3]
                ch = 0 if chan == 'A' else 1
                data = msg[4:].split()
                trace = []
                for word in data:
                    adc = int(word[1:], 16)
                    if adc >= 0x0800: adc -= 0x1000
                    trace.append(adc)
                self.app.AddTrace(ch, trace)
                self.capture_page += 1
                if self.capture_page < self.capture_max:
                    self.app.IifCmd('iic%c%02x' % ('ab'[ch], self.capture_page))
                elif chan == 'A' and self.capb.IsChecked():
                    self.capture_page = 0
                    self.app.IifCmd('iicb00')
                else:
                    self.app.PlotTrace()
                    self.SetStatusText('ADC waveform plot ready')
                    self.plot.Enable(True)
            else:
                pass # ignore echo (IIEC) command
        else: # not a command acknowledge
            if msg.startswith('Accumulator Ready'):
                if self.accumulating == self.ACCUM_START: # throw first capture away
                    self.accumulating = self.ACCUM_ACTIVE
                    self.app.IifCmd('iiac')
                    self.integrate_stop_time = time.time() + self.intDuration.GetValue()
                    if self.int_period:
                        self.intTimer.Start(1000 * self.int_period)
                else:
                    self.app.IifCmd('iiar')
            elif msg.startswith('Reset'):
                # re-load parameters
                self.app.IifCmd('iild','iiga','iigb','iipa','iipb','iida','iidc')
            else:
                self.SetStatusText('IIF message: ' + msg)
    # End of CorrelatorWin
                

class CorrelatorApp (wx.App):
    def __init__(self, dev, rec):
        wx.App.__init__(self)
        self.iif = serial.Serial(dev, 115200, rtscts=1)
        self.cmdQ = []          # queued IIF commands
        self.cmd = None         # current IIF command
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimeout, self.timer)
        self.win = CorrelatorWin('IIF Correlator', self, rec)
        self.win.Centre()
        self.win.Show(True)
        self.SetTopWindow(self.win)
        self.plt = PlotWin('IIF Plot')
        self.ClrTrace()
        self.ClrAccum()
        thread.start_new_thread(self.IifThread, ())
    def IifThread(self):
        '''Thread to listen to IIF serial port and
        generate an IifEvent for each IIF message read'''
        while True:
            msg = self.iif.readline()
            if not msg: break
            wx.CallAfter(self.win.OnIif, msg.strip())
    def IifWrite(self, cmd):
        self.cmd = cmd[:4].upper() # for checking acknowledge
        self.iif.write(cmd + '\r')
        self.timer.Start(100, oneShot=True) # 100mS timeout
    def IifCmd(self, *cmds):
        '''Write cmd to IIF or, if cmd pending, queue it'''
        for cmd in cmds:
            if not self.cmd:
                self.IifWrite(cmd)
            else:
                self.cmdQ.append(cmd)
    def IifAck(self, msg):
        '''Check if msg is acknowledge to pending IIF command.
        Send next queued command if it is'''
        if self.cmd == msg[:4]:
            self.cmd = None
            self.timer.Stop()
            # current command is acknowledged, send next queued command
            if self.cmdQ:
                cmd, self.cmdQ = self.cmdQ[0], self.cmdQ[1:]
                self.IifWrite(cmd)
            return True
        return False
    def OnTimeout(self, event):
        '''Failed to get IIF command acknowledge'''
        self.win.SetStatusText('Failed command: %s' % self.cmd)
        if self.cmdQ:
            cmd, self.cmdQ = self.cmdQ[0], self.cmdQ[1:]
            self.IifWrite(cmd)
        else:
            self.cmd = None;
    def AddTrace(self, chan, data):
        '''Add ADC waveform trace to buffer'''
        trace = self.trace[chan]
        start = len(trace)
        for adc in data:
            trace.append([start * 5e-3, adc])
            start += 1
    def ClrTrace(self):
        '''Clear ADC waveform buffer'''
        self.trace = [[],[]]
    def PlotTrace(self):
        '''Plot ADC waveforms'''
        self.plt.PlotTrace(self.trace[0], self.trace[1])
    def ClrAccum(self):
        '''Clear accumulator history buffer'''
        self.accum_start = 0
        self.accum_sec = 0
        self.accum = []
    def PlotAccum(self, accum):
        '''Plot accumulator history'''
        if self.accum_start:
            sec = time.time() - self.accum_start
        else:
            self.accum_start = time.time()
            sec = 0
        # update plot at most once per second
        if sec >= self.accum_sec:
            self.accum.append([sec, float(accum)])
            if len(self.accum) > 1:
                self.plt.PlotAccum(self.accum)
            self.accum_sec = sec + 1
if __name__ == '__main__':
    dev = '/dev/ttyM3'
    rec = False
    for arg in sys.argv:
        if arg[:2] == '-d':
            dev = arg[2:]
        elif arg == '-r':
            rec = True
        elif arg == '-h' or arg == '--help':
            print 'Usage: %s [-r] [-d<serial-device>]' % sys.argv[0]
            print '       %s (-h | --help)' % sys.argv[0]
            print 'Options:'
            print '       -r : Enable recording at startup'
            print '       -d<serial-device> : Use <serial-device> to connect to IIF module'
            print '       -h | --help : Print this help message and exit'
            exit(1)
    CorrelatorApp(dev, rec).MainLoop()

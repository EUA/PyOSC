#!/usr/bin/env python

#    pyOSC python Oscilloscope GUI for semifluid's 18F2550 HID USB machine
#    Copyright (C) 2010  Erdem U. Altunyurt, donated to semifluids.com

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Project's Home Page http://www.semifluid.com/?p=24

#    Version 0.1 Initial Release

import wx,usb
from wx import xrc

def calc_crc( oldcrc, newbyte ):
  shift_reg=oldcrc
  for j in range(0,8):
   data_bit = (newbyte >> j) & 0x01
   sr_lsb = shift_reg & 0x01
   fb_bit = (data_bit ^ sr_lsb) & 0x01
   shift_reg = shift_reg >> 1
   if (fb_bit):
    shift_reg = shift_reg ^ 0x8c
  return shift_reg

def crc8( str ):
   crc=0
   for s in str:
      crc=calc_crc(crc,s)
   return crc

class MyApp(wx.App):
   def OnInit(self):
      self.res = xrc.XmlResource('pyosc.xrc')
      self.init_frame()
      return True
   def init_frame(self):
      self.frame = self.res.LoadFrame(None, 'pyosc')
      self.oscDC = xrc.XRCCTRL(self.frame, 'oscDC')
      self.data_cache=[-1]*512
      self.txt_USBStatus = xrc.XRCCTRL(self.frame, 'txt_USBStatus')
      self.txt_ReadData = xrc.XRCCTRL(self.frame, 'txt_ReadData')
      self.chk_useCRC = xrc.XRCCTRL(self.frame, 'chk_useCRC')
      self.chk_pause = xrc.XRCCTRL(self.frame, 'chk_pause')
      self.period = 0.016

      self.txt_SendData=[]
      for i in range(0,8):
         self.txt_SendData.append( xrc.XRCCTRL(self.frame, 'txt_SendData'+str(i)) )
      self.oscDC.Bind(wx.EVT_PAINT, self.on_paint)
      self.frame.Bind(wx.EVT_BUTTON, self.OnGetDataAsap, id=xrc.XRCID('btn_getdata_asap'))
      self.frame.Bind(wx.EVT_BUTTON, self.OnGetData, id=xrc.XRCID('btn_getdata'))
      self.frame.Bind(wx.EVT_BUTTON, self.OnGetRamData, id=xrc.XRCID('btn_getramdata'))
      self.frame.Bind(wx.EVT_BUTTON, self.OnReadWrite, id=xrc.XRCID('btn_readwrite'))
      self.frame.Bind(wx.EVT_CHECKBOX, self.OnUseCRC, id=xrc.XRCID('chk_useCRC'))
      self.frame.Bind(wx.EVT_CHECKBOX, self.OnContunious, id=xrc.XRCID('chk_contunious'))
      self.frame.Bind(wx.EVT_SCROLL, self.on_paint, id=xrc.XRCID('scroll_V1'))
      self.frame.Bind(wx.EVT_SCROLL, self.on_paint, id=xrc.XRCID('scroll_V2'))
      self.frame.Bind(wx.EVT_SCROLL, self.on_paint, id=xrc.XRCID('scroll_H1'))
      self.frame.Bind(wx.EVT_SCROLL, self.on_paint, id=xrc.XRCID('scroll_H2'))
      self.frame.Bind(wx.EVT_IDLE, self.OnIdle )

      self.dev=None
      self.frame.Show()

   def OnIdle(self,event):
      if self.dev == None:
         try:
            self.dev=usb.core.find(idVendor=0x461,idProduct=0x20)
         except usb.core.USBError:
            print 'USBError'
         if self.dev != None:
            try:
               if  self.dev.is_kernel_driver_active(0):
                  self.dev.detach_kernel_driver(0)
               self.dev._Device__set_def_tmo(10000)
            except usb.core.USBError:
               print 'USBError : Disconnection?'
               self.dev = None
            self.txt_USBStatus.SetLabel('Connected')
            self.txt_USBStatus.SetForegroundColour('dark green')
         else:
            self.txt_USBStatus.SetLabel('Disconnected')
            self.txt_USBStatus.SetForegroundColour('indian red')
      pass

   def on_paint(self, event, cleardata=False):
      dc = wx.PaintDC(self.oscDC)
      dc.SetDeviceOrigin(0,dc.GetSize()[1]-1)
      dc.SetAxisOrientation(True,True)
      dc.SetBackground( wx.Brush('black') )
      dc.SetBrush( wx.Brush('black') )
      dc.Clear()
      dc.SetPen(wx.Pen('dim gray', 1))
#      period = 0
#      if self.dev != None:
#         self.WriteData( [6,255,255,255,255,255,255,255] )
#         rdd = self.ReadData( )
#         period = rdd[2]*256 + rdd[3]

      for v in range(0,256,51):#draws voltage lines
         v=v
         dc.DrawLine(0, v, dc.GetSize()[0], v)

      h1 = xrc.XRCCTRL(self.frame,'scroll_H1').GetThumbPosition()
      h2 = xrc.XRCCTRL(self.frame,'scroll_H2').GetThumbPosition()
      v1 = xrc.XRCCTRL(self.frame,'scroll_V1').GetThumbPosition()
      v2 = xrc.XRCCTRL(self.frame,'scroll_V2').GetThumbPosition()

      dc.SetPen(wx.Pen(wx.Colour(0xff,0x70,0x70), 1))
      if v1: dc.DrawLine(0, v1, dc.GetSize()[0], v1)
      if v2: dc.DrawLine(0, v2, dc.GetSize()[0], v2)
      dc.SetPen(wx.Pen(wx.Colour(0x70,0x70,0xff), 1))
      if h1: dc.DrawLine(h1, 0, h1, dc.GetSize()[1])
      if h2: dc.DrawLine(h2, 0, h2, dc.GetSize()[1])

      xrc.XRCCTRL(self.frame,'txt_voltage').SetLabel( '%0.3fV' % (abs(v1-v2)*5.0/255)  )
      xrc.XRCCTRL(self.frame,'txt_period').SetLabel( '%0.3fms' % (abs(h1-h2)*self.period)  )

      dc.SetPen(wx.Pen('green', 1))
      x=0
      if not cleardata:
         for y in self.data_cache:
            if x != 0:
               if y>=0 : dc.DrawLine(x-1, oldy, x, y)
            x+=1
            oldy = y
      else:
         self.data_cache = [-1]*512

   def OnUseCRC(self,event):
      wrt = [11,255,255,255,255,255,255,255]
      if event.Checked(): wrt[0]=10
      self.WriteData( wrt )
      self.ReadData( )

   def OnContunious(self,event):
      if event.Checked():
         xrc.XRCCTRL(self.frame, 'btn_getdata_asap').Enable(False)
         xrc.XRCCTRL(self.frame, 'btn_getdata').Enable(False)
         chk_contunious = xrc.XRCCTRL(self.frame, 'chk_contunious')
         x,y=0,0
         dc = wx.PaintDC(self.oscDC)
         dc.SetDeviceOrigin(0,dc.GetSize()[1]-1)
         dc.SetAxisOrientation(True,True)
         self.on_paint( event )
         dc.SetPen(wx.Pen('green', 1))
         while chk_contunious.GetValue():
            wx.Yield()
            if self.chk_pause.GetValue():
     	         continue
            if x == 0:
               self.on_paint(event, cleardata=True)
            self.WriteData([04,255,255,255,255,255,255,255])
            data = self.ReadData()
            if x != 0:
               dc.DrawLine(x-1, y, x, data[2] )
            x+=1
            y=data[2]
            if x < 512:
               self.data_cache[x] = y
            else:
               print x
#            if x == dc.GetSize()[0]:
            if x == 511:
               x=0

      else:
         xrc.XRCCTRL(self.frame, 'btn_getdata_asap').Enable(True)
         xrc.XRCCTRL(self.frame, 'btn_getdata').Enable(True)

   def ReadData(self):
      while True:
         try:
            data = self.dev.read(0x81,8)
            break
         except usb.core.USBError:
            pass

      CRC=''
      if self.chk_useCRC.GetValue():
         if crc8( data[:-1] ) == data[-1]:
            CRC='CRC OK'
         else:
            CRC='BAD CRC'
      self.txt_ReadData.SetLabel( ''.join([ str(s)+' ' for s in data.tolist()]) + CRC )
      return data

   def WriteData(self, data ):
      for i in range(0,8):
         self.txt_SendData[i].ChangeValue( str(data[i]) )
      bytes=0
      try:
         bytes=self.dev.write(1, data)
      except usb.core.USBError:
         print 'USBError : Disconnection?'
         self.dev=None
      return bytes

   def OnReadWrite(self, event):
      if self.chk_pause.GetValue() : return
      wrt=[]
      for r in self.txt_SendData:
         wrt.append( int(r.GetValue()) )
      self.WriteData(wrt)
      self.ReadData()

   def OnGetData(self, event):
      if self.chk_pause.GetValue() : return
      del self.data_cache
      self.data_cache=[-1]*600
      txt_latency = xrc.XRCCTRL(self.frame, 'txt_latency')
      if xrc.XRCCTRL(self.frame, 'radio_latency_us').GetValue():
         val = int(txt_latency.GetValue())
         if val < 250:
            txt_latency.SetValue( '250' )
            val=250
         wx.Yield()
         self.period=val*0.001
         self.WriteData( [12,2,0,(val&0xFF00) >> 8, val & 0x00FF,255,255,255] )
         self.ReadData()
      else:
         val = int(txt_latency.GetValue())
         self.period=val
         self.WriteData( [7,2,0,(val&0xFF00) >> 8, val & 0x00FF,255,255,255] )
         self.ReadData()
         wx.Yield()
         wx.Sleep( (val * 512 )/ 1000 ) #Wait x some secconds until job is compleeted.
      self.OnGetRamData(event)

   def OnGetDataAsap(self, event):
      if self.chk_pause.GetValue() : return
      del self.data_cache
      self.data_cache=[-1]*600
      self.WriteData( [5,2,0,255,255,255,255,255] )
      self.ReadData()
      self.period=0.016
      self.OnGetRamData(event)

   def OnGetRamData(self,event):
      if self.chk_pause.GetValue() : return
      del self.data_cache
      self.data_cache=[-1]*600
      dc = wx.PaintDC(self.oscDC)
      dc.SetDeviceOrigin(0,dc.GetSize()[1]-1)
      dc.SetAxisOrientation(True,True)
      self.on_paint( event )
      dc.SetPen(wx.Pen('green', 1))

      for i in range(0,512):
         self.WriteData( [2,i/256,i%256,255,255,255,255,255] )
         tmp=self.ReadData()
         v=tmp[4]
         if i != 0:
            dc.DrawLine(i-1, y, i, v )
         y = v
         self.data_cache[i] = v
         wx.Yield()

      xrc.XRCCTRL(self.frame, 'txt_debug').ChangeValue(str(self.data_cache[:512]))

if __name__ == '__main__':
   app = MyApp(False)
   app.MainLoop()


'''
Created on Dec 3, 2015
@author: Dagomi
'''
#!/usr/bin/env python
import os
import gi
import psutil
import threading
from xml.etree import ElementTree
from urllib import urlopen 
#http://www.bok.net/dash/tears_of_steel/cleartext/stream.mpd
#http://localhost/dash/trik_audio_video/stream.mpd
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, Gtk, GdkX11 , GstVideo 

Gst.init(None)

#--- Select environment (True)/Simulation (False)
SELECTOR = False
URLPRUEBAS = 'http://www.bok.net/dash/tears_of_steel/cleartext/stream.mpd'

# -- Varibles---

BUFFERSIZE =    6000000000
PREROLLBUFFER = 3000000000



class GTK_Main(object):
    
    def __init__(self):
        GObject.threads_init()
        self.VARIABLE_ESTADO_BATERIA_TEMPORAL = 0
        self.PLAY = 0
        self.indice = 0
        self.UI() # Launch the User Interface
        self.Dashplayer() # Launch the Gst Client

        
    
    def UI (self):
        #UI
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("MPEG-DASH Player")
        window.set_default_size(430 , 250)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        window.set_border_width(10)
        
        # horizontal separator
        hseparator_scenario = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vseparator_sliders = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        vseparator_simulation = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        vbox = Gtk.VBox()
        window.add(vbox)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)
        
        sliders = Gtk.HBox()
        vbox.pack_end(sliders, False, False, 0)
        
        table = Gtk.Table(7, 8, False)
        table.set_col_spacings(25)
        sliders.add(table)

        #Labels
        #Sliders
        label_top_left = Gtk.Label(label="Buffer Ocupancy (%)" )
        label_top_right = Gtk.Label(label="Battery Level (%)")
        label_bottom_left = Gtk.Label(label="CPU Load (%)")
        label_bottom_right = Gtk.Label(label="Available Bandwidth (Kbs/s)")
        
        #Simulations
        self.label_Simulation = Gtk.Label(label="Simulation")
        self.label_Buffer_Sim = Gtk.Label(label="Buffer is 0 %")
        self.label_Battery_state_Sim = Gtk.Label(label="Battery supply")
        self.label_Battery_Sim = Gtk.Label(label="Battery is 0 %")
        self.label_CPU_Sim = Gtk.Label(label="CPU is 0 %")
        self.label_BW_Sim = Gtk.Label(label="BW is 0 Kbs")
        
        #Tresholds
        self.label_Tresholds = Gtk.Label(label="Tresholds")
        self.label_Tresholds_Buffer = Gtk.Label(label="Buffer (0-100) % :")
        self.label_Tresholds_Battery = Gtk.Label(label="Battery (0-100) % :")
        self.label_Tresholds_CPU = Gtk.Label(label="CPU (0-100) % :")
        
        
       
        self.bufferTreshold = Gtk.Entry()
        self.bufferTreshold.set_max_length(3)
        self.batteryTreshold = Gtk.Entry()
        self.batteryTreshold.set_max_length(3)
        self.cpuTreshold = Gtk.Entry()
        self.cpuTreshold.set_max_length(3)

        # in the grid:
        # attach the first label in the top left corner   (left_attach,right_attach,top_attach,bottom_attach)
        #separators
        table.attach(hseparator_scenario,           0, 8, 0, 1)
        table.attach(vseparator_sliders,            2, 3, 0, 7)
        table.attach(vseparator_simulation,         5, 6, 0, 7)
        table.attach(label_top_left,                0, 1, 1, 2)
        table.attach(label_top_right,               1, 2, 1, 2)
        table.attach(label_bottom_left,             0, 1, 4, 5)
        table.attach(label_bottom_right,            1, 2, 4, 5)
        #sliders / buttons
        table.attach(self.label_Simulation,         3, 4, 1, 2)        
        table.attach(self.label_Buffer_Sim,         3, 4, 2, 3)
        table.attach(self.label_Battery_Sim,        3, 4, 3, 4)
        table.attach(self.label_Battery_state_Sim,  3, 4, 4, 5)
        table.attach(self.label_CPU_Sim,            3, 4, 5, 6)
        table.attach(self.label_BW_Sim,             3, 4, 6, 7)
        #text entry for tresholds
        table.attach(self.label_Tresholds,          7, 8, 1, 2)        
        table.attach(self.bufferTreshold,           7, 8, 2, 3)
        table.attach(self.batteryTreshold,          7, 8, 3, 4)
        table.attach(self.cpuTreshold,              7, 8, 4, 5)

        #labels tresholds
        table.attach(self.label_Tresholds_Buffer,   6, 7, 2, 3)
        table.attach(self.label_Tresholds_Battery,  6, 7, 3, 4)
        table.attach(self.label_Tresholds_CPU,      6, 7, 4, 5)
        
        #Togle button Power supply
        PowerSupplyButton = Gtk.CheckButton("Charger")
        PowerSupplyButton.connect("toggled", self.on_button_power_supply, "1")
        table.attach (PowerSupplyButton, 1, 2, 2, 3)

        #Slider 1 Buffer
        self.Buffer_Sim = Gtk.SpinButton()
        adjustmentBuffer = Gtk.Adjustment(0, 0, 100, 1, 10, 0) 
        self.Buffer_Sim.set_adjustment(adjustmentBuffer)
        table.attach(self.Buffer_Sim, 0, 1, 3, 4)
        self.Buffer_Sim.connect("value-changed", self.BufferChange)
   
        #Slider 2 CPU
        self.CPU_Sim = Gtk.SpinButton()
        adjustmentCPU = Gtk.Adjustment(0, 0, 100, 1, 10, 0) 
        self.CPU_Sim.set_adjustment(adjustmentCPU)
        table.attach(self.CPU_Sim, 0, 1, 5, 6)
        self.CPU_Sim.connect("value-changed", self.CPUChange)
         
        #Slider 3 BW
        self.BW_Sim = Gtk.SpinButton()
        adjustmentBW = Gtk.Adjustment(0, 0, 50000, 100, 10, 0) #1 Kbyte = bits 8192
        self.BW_Sim.set_adjustment(adjustmentBW)
        table.attach(self.BW_Sim, 1, 2,5,6)
        self.BW_Sim.connect("value-changed", self.BWChange)
        
        #Slider 4 Battery
        self.Battery_Sim = Gtk.SpinButton()
        adjustmentBatt = Gtk.Adjustment(0, 0, 100, 1, 10, 0) 
        self.Battery_Sim.set_adjustment(adjustmentBatt)
        table.attach(self.Battery_Sim, 1, 2, 3, 4)
        self.Battery_Sim.connect("value-changed", self.BatteryChange)
        
        self.inputMpdUrl = Gtk.Entry()
        hbox.add(self.inputMpdUrl)
        self.button_open = Gtk.Button("Open")
        hbox.pack_start(self.button_open, False, False, 0)
        self.button_open.connect("clicked", self.open_mpd)
        
        self.button_pause = Gtk.Button("Pause")
        hbox.pack_start(self.button_pause, False, False, 0)
        self.button_pause.connect("clicked", self.play_pause)
        
        self.movie_window = Gtk.DrawingArea()
        vbox.add(self.movie_window)
        window.show_all()
    
    def Dashplayer (self):
        #Gstreamer
  
        self.player = Gst.Pipeline.new("player")
        self.source = Gst.ElementFactory.make("souphttpsrc", "http-src")
        self.dashdemuxer = Gst.ElementFactory.make("dashdemux", "dashdemux")
        
        self.videoqueue = Gst.ElementFactory.make("queue2", "video_queue")
        
        
        self.videoqueue.set_property ( "use-buffering", True)
        self.videoqueue.set_property ("max-size-buffers",0)
        self.videoqueue.set_property ("high-percent",  100)
        self.videoqueue.set_property ("low-percent",  10,)
        self.videoqueue.set_property ("max-size-time", BUFFERSIZE)
        
        self.videodemuxer = Gst.ElementFactory.make("qtdemux", "videodemuxer")
        self.videodecoder = Gst.ElementFactory.make ("h264parse","video_decoder")
        self.videoconvert = Gst.ElementFactory.make ("avdec_h264","video_convert")
        self.videosink = Gst.ElementFactory.make("autovideosink", "video_sink")

        self.audioqueue = Gst.ElementFactory.make("queue2", "audio_queue")
        self.audioqueue.set_property ( "use-buffering", True)
        self.audioqueue.set_property ("max-size-buffers",0)
        self.audioqueue.set_property ("high-percent",  100)
        self.audioqueue.set_property ("low-percent",  10,)
        self.audioqueue.set_property ("max-size-time", BUFFERSIZE)
        
        self.audiodemuxer = Gst.ElementFactory.make("qtdemux", "audio_demuxer")
        self.audiodecoder = Gst.ElementFactory.make("aacparse", "audio_decoder")
        self.audioconv = Gst.ElementFactory.make("faad", "audio_converter")
        self.audiosink = Gst.ElementFactory.make("autoaudiosink", "audio-output")
        
        self.textoverlay = Gst.ElementFactory.make("textoverlay", "text")
 
        self.player.add(self.source)
        self.player.add(self.dashdemuxer)
        self.player.add(self.videodemuxer)
        self.player.add(self.audiodemuxer)
        self.player.add(self.videodecoder)
        self.player.add(self.audiodecoder)
        self.player.add(self.audioconv)
        self.player.add(self.audiosink)
        self.player.add(self.videosink)
        self.player.add(self.videoqueue)
        self.player.add(self.audioqueue)
        self.player.add(self.videoconvert)
        
        self.player.add(self.textoverlay)
        
        self.source.link(self.dashdemuxer)
        self.dashdemuxer.link(self.videodemuxer)
        self.dashdemuxer.link(self.audiodemuxer)
        
        
        self.videoqueue.link(self.videodecoder)
        
        #self.videodecoder.link(self.videoconvert)
        self.videodecoder.link(self.videoconvert)
        self.videoconvert.link(self.textoverlay)
        self.textoverlay.link(self.videosink)
        
        self.audioqueue.link(self.audiodecoder)
        self.audiodecoder.link(self.audioconv)
        self.audioconv.link(self.audiosink)
        
        #Handlers
        self.dashdemuxer.connect("pad-added",self.dashdemuxer_callback)
        self.videodemuxer.connect("pad-added",self.videodemuxer_callback)
        self.audiodemuxer.connect("pad-added",self.audiodemuxer_callback)
        
        
        self.Algorithm()

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)
        
    def open_mpd(self, w):
        #self.environment()
        self.PLAY = 1
        if self.button_open.get_label() == "Play":
                self.player.set_state(Gst.State.PLAYING)
        #check button value 
        if self.button_open.get_label() == "Open":
            self.filepath = URLPRUEBAS
            #filepath = self.inputMpdUrl.get_text()
            if self.filepath.startswith("http://"):
                print ('Url OK')
                self.button_open.set_label("Play")
                self.player.get_by_name("http-src").set_property("location", self.filepath)
                self.loadTemplateTile() #Obtain MPD parameters
                self.player.set_state(Gst.State.PLAYING)
            else:
                print ('Input a valid url')
                self.player.set_state(Gst.State.READY)
                self.button_open.set_label("Open")
                    
        
    def play_pause(self, w):
        print ('Pause')
        self.player.set_state(Gst.State.PAUSED)
        
    def on_message(self, bus, message):

        t = message.type
        level = self.videoqueue.get_property("current-level-time")
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")
        
        if t == Gst.MessageType.BUFFERING:
            if level <= PREROLLBUFFER:
                    print ("Buffering... %d" % level)
                    self.player.set_state(Gst.State.PAUSED)
                   
            else:
                self.player.set_state(Gst.State.PLAYING)
            
    
    def on_sync_message(self, bus, message):
        
        if message.get_structure().get_name() == 'prepare-window-handle':
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            xid = self.movie_window.get_property('window').get_xid()
            imagesink.set_window_handle(xid)
            
        if message.structure is None:
            return False
        if message.structure.get_name() == "prepare-xwindow-id":
            Gtk.gdk.threads_enter()
            Gtk.gdk.display_get_default().sync()
            win_id = self.movie_window.get_property('window').get_xid()
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(win_id)
            Gtk.gdk.threads_leave()
                
    def dashdemuxer_callback(self, demuxer, pad):
            print ('demuxer_call_bak')
            print('valor %s' % pad.get_name())
            if pad.get_name() == "ghostpad0":
                qv_pad = self.videodemuxer.get_static_pad("sink")
                pad.link(qv_pad)
                print ('link video')
            elif pad.get_name() == "ghostpad1":
                qa_pad = self.audiodemuxer.get_static_pad("sink")
                pad.link(qa_pad)
                print ('link audio')

    def videodemuxer_callback(self, demuxer, pad):
            print ('videodemuxer_callback')
            print('valor %s' % pad.get_name())
            if pad.get_name() == "video_0":
                qv_pad = self.videoqueue.get_static_pad("sink")
                pad.link(qv_pad)
                print ('link video')
            elif pad.get_name() == "audio_0":
                qa_pad = self.audioqueue.get_static_pad("sink")
                pad.link(qa_pad)
                print ('link audio')
    
    def audiodemuxer_callback(self, demuxer, pad):
            print ('audiodemuxer_callback')
            print('valor %s' % pad.get_name())
            if pad.get_name() == "video_0":
                qv_pad = self.videoqueue.get_static_pad("sink")
                pad.link(qv_pad)
                print ('link video')
            elif pad.get_name() == "audio_0":
                qa_pad = self.audioqueue.get_static_pad("sink")
                pad.link(qa_pad)
                print ('link audio')

    '''
    UI
    '''
    def on_button_power_supply(self, button, name):
        if SELECTOR:
            print ("environment Batt State")
            Battery = []
            Battery = self.environmentBattery()
            self.dashdemuxer.set_property("system-battery-state", int(str(Battery[1])))
            self.dashdemuxer.set_property("system-battery-charge", int(str(Battery[0])))
        else:
            #print ("Simulation Batt State") 
            if button.get_active():
                self.label_Battery_state_Sim.set_text("Power supply")
                self.VARIABLE_ESTADO_BATERIA_TEMPORAL = 1
            else:
                self.label_Battery_state_Sim.set_text("Battery supply")
                self.VARIABLE_ESTADO_BATERIA_TEMPORAL = 0
                
    def BatteryChange(self, event):
        if SELECTOR:
            print ("environment Batt Level")
            Battery = []
            Battery = self.environmentBattery()
            self.SYSTEM_BATTERY_CHARGE = int(str(Battery[1]))
            
        else:
            self.label_Battery_Sim.set_text("Battery is " + str(int(self.Battery_Sim.get_value())) + "%")

    def BufferChange(self, event):
        if SELECTOR:
            print ("environment Buffer (not implemented yet)")
        else:
        
            '''
            0         Threshhold     100
            |------------|-----------|
                Danger        Optimal
             '''
            self.label_Buffer_Sim.set_text("Buffer is " + str(int(self.Buffer_Sim.get_value())) + "%")

                
    def CPUChange(self, event):
        if SELECTOR:
            print ("environment CPU Load ")
        else:
            #print ("Simulation CPU Load")
            self.label_CPU_Sim.set_text("CPU is " + str(int(self.CPU_Sim.get_value())) + "%" )

    def BWChange(self, event):    
        self.label_BW_Sim.set_text(("BW is %0.3f Mb/s") % (int(self.BW_Sim.get_value())*0.0009765625))  
    
    def environmentBattery (self):
        BATT_NOW     =   "/sys/class/power_supply/BAT0/charge_now"
        BATT_FULL    =  "/sys/class/power_supply/BAT0/charge_full"
        BATT_STATUS  =     "/sys/class/power_supply/BAT0/status"    
    
        full = open(BATT_FULL, 'r')
        full_value = full.read()
        
        now = open(BATT_NOW, 'r')
        now_value = now.read()
        
        status = open(BATT_STATUS, 'r')
        status_value = status.read()
        
        if 'Charging' in  status_value:
            statusBattery = 'Charging'
        
        elif 'Discharging' in status_value:
            statusBattery = 'Discharging'
        
        elif 'Full' in status_value:
            statusBattery = ' Full '

        BatteryLoad = (int(now_value) / ( int(full_value)/100))

        full.close()
        now.close()
        status.close()
        
        return (BatteryLoad , statusBattery )
        
    

    def loadTemplateTile(self):
        ADAPTATIONSET = []
        self.BANDWITH_MPD = []
        #Load Xml
        manifestXmlTree = ElementTree.parse(urlopen(self.filepath))
        root = manifestXmlTree.getroot()
        tag = root.tag
        xmlns = tag.replace("MPD", "")
        PERIOD = root[0]
        
        for index in range (0,(len(PERIOD)),1):

            ADAPTATIONSET.append(PERIOD[index])
            ADAPTATIONSETATTRIB =(ADAPTATIONSET[index].attrib)
            if ADAPTATIONSETATTRIB["mimeType"] == "video/mp4":
                ADAPTATIONSET_VIDEO = ADAPTATIONSET[index]
                
        REPRESENTATION = (ADAPTATIONSET_VIDEO.findall( xmlns +"Representation"))
        
        for index in range (0,len(REPRESENTATION),1):
            REPRESENTATIONATTRIB = REPRESENTATION[index].attrib
            self.BANDWITH_MPD.append(REPRESENTATIONATTRIB['bandwidth'])
        print self.BANDWITH_MPD
        
    def Algorithm (self):
        
        threading.Timer(2.0, self.Algorithm).start()
        print ("--- Algoritmo ---")
        #Check threshold imputs
        if self.bufferTreshold.get_text() == "":
            MAX_CPU     = 85
            print "bufferTreshold is empty set as default: %s " %  MAX_CPU
        else:
            MAX_CPU = int(self.bufferTreshold.get_text())
            print "bufferTreshold set as : %s " %  MAX_CPU
            
        if self.batteryTreshold.get_text() == "":
            VERY_LOW_BATT_LOAD = 5
            print "bufferTreshold is empty as default: %s " %  VERY_LOW_BATT_LOAD 
        else:    
            VERY_LOW_BATT_LOAD = int(self.batteryTreshold.get_text())   
            print "bufferTreshold set as: %s " %  VERY_LOW_BATT_LOAD 
        if self.cpuTreshold.get_text() == "":
            MIN_BUFFER      = 50
            print "bufferTreshold is empty as default: %s " %  MIN_BUFFER   
        else:
            MIN_BUFFER = int(self.cpuTreshold.get_text())
            print "bufferTreshold set default: %s " %  MIN_BUFFER   
        
        
        #environment (at the momenr only simulated conditions)
        SYSTEMCPU   = int(self.CPU_Sim.get_value())
        SYSTEM_BATTERY_STATE = self.VARIABLE_ESTADO_BATERIA_TEMPORAL
        SYSTEM_BATTERY_CHARGE = int(self.Battery_Sim.get_value())
        SYSTEM_BUFFER = int(self.Buffer_Sim.get_value())
        
        
        if SYSTEMCPU > MAX_CPU :
            print ("System CPU overload")
            self.previousSegmentQuality()
            #Calidad minima
        
        elif SYSTEMCPU <= MAX_CPU :
            print ("System CPU normal")
            #Uso normal del algoritmo
            #Check Battery
            if SYSTEM_BATTERY_STATE == 0: #Uso de la Bateria
                print ("uso bateria")
                #if SYSTEM_BATTERY_CHARGE < MIN_BATT_LOAD:
                if SYSTEM_BATTERY_CHARGE <= VERY_LOW_BATT_LOAD:
                        #usar text overlay
                        self.textOverlayFunction("Battery below: %s" % VERY_LOW_BATT_LOAD )
                        print ("Bateria baja text overlay")
                        if SYSTEM_BATTERY_CHARGE <= VERY_LOW_BATT_LOAD:
                            print ("calidad minima y text overlay")
                        elif SYSTEM_BATTERY_CHARGE > VERY_LOW_BATT_LOAD:
                            #Rutina Buffer
                            if SYSTEM_BUFFER <= MIN_BUFFER :
                                print ("Buffer bajo")
                                #bajo una calidad
                            elif SYSTEM_BUFFER > MIN_BUFFER:
                                print ("Buffer OK")
                                #selecciono la mejor calidad seun el BW
                                self.nextSegmentQuality()
                elif SYSTEM_BATTERY_CHARGE > VERY_LOW_BATT_LOAD:
                    self.textOverlayFunction("")
                    print ("Bateria normal")
                                #Rutina Buffer
                    if SYSTEM_BUFFER <= MIN_BUFFER :
                        print ("Buffer bajo")
                        self.previousSegmentQuality()
                    elif SYSTEM_BUFFER > MIN_BUFFER:
                        print ("Buffer OK")
                        #selecciono la mejor calidad seun el BW
                        self.nextSegmentQuality()
            elif SYSTEM_BATTERY_STATE == 1: #Uso del cargador
                print ("uso cargador")
                self.textOverlayFunction("")
                #Rutina Buffer
                if SYSTEM_BUFFER <= MIN_BUFFER :
                    print ("Buffer bajo calidades pregresivamente:")
                    self.previousSegmentQuality()
                elif SYSTEM_BUFFER > MIN_BUFFER:
                    print ("Buffer OK")
                    #selecciono la mejor calidad seun el BW
                    self.nextSegmentQuality()    
 
    def nextSegmentQuality(self):
        if self.PLAY == 1:
            #Select the best Quality in therms of BW
            for i in range (0,len(self.BANDWITH_MPD),1):
                if int(self.BW_Sim.get_value()) >= int(self.BANDWITH_MPD[i]):
                    action = "subo"
                    self.indice = i
                    SelectRepresentation =  int(self.BANDWITH_MPD[i])
                elif  int(self.BW_Sim.get_value()) < int(self.BANDWITH_MPD[0]):
                    action = "bajo"
                    SelectRepresentation =  int(self.BANDWITH_MPD[0])
                    self.indice = 0
            print (" %s de calidad") % action
            print SelectRepresentation
        
    
    def previousSegmentQuality(self):
        if self.PLAY == 1:
            print ("indice calidad %s " ) % self.indice
            calidadactual = self.indice
            if calidadactual == 0 :
                print ("ya estoy en la mas baja")
            else:
                siguientecalidad = calidadactual - 1
                print siguientecalidad
        
        #Aqui llamo al demux
        #self.dashdemuxer.set_property("bw-sim", int(SelectRepresentation))   
    
    def textOverlayFunction (self, text):
            self.textoverlay.set_property("halignment", 0)
            self.textoverlay.set_property("valignment", 2)
            self.textoverlay.set_property("auto-resize", False)
            self.textoverlay.set_property("text", text)
        
if __name__ == "__main__":

    GTK_Main()# run Python Class
    Gtk.main()# run Ui
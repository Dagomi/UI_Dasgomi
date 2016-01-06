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

#--- Select Enviorment (True)/Simulation (False)
SELECTOR = False
URLPRUEBAS = 'http://localhost/dash/multirate_3/stream.mpd'

# -- Varibles---

BUFFERSIZE =    6000000000
PREROLLBUFFER = 3000000000
BUFFERTHRESHOLD = 50 # en %

class GTK_Main(object):
    
    def __init__(self):
        
        self.VARIABLE_ESTADO_BATERIA_TEMPORAL = 0
        
        self.UI() # Launch the User Interface
        self.Algorithm()
        self.Dashplayer() # Launch the Gst Client
        self.readEnviorment() # Readenviorment first time and launch the thread
                              # at the moment an unicv thread scheduling all.
        
    
    def UI (self):
        #UI
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("MPEG-DASH Player")
        window.set_default_size(430 , 250)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        window.set_border_width(10)
        
        # horizontal separator
        hseparator_scenario = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        vbox = Gtk.VBox()
        window.add(vbox)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)
        
        sliders = Gtk.HBox()
        vbox.pack_end(sliders, False, False, 0)
        
        table = Gtk.Table(7, 4, False)
        table.set_col_spacings(25)
        sliders.add(table)


        
        
        #Labels
        #Sliders
        label_top_left = Gtk.Label(label="Buffer Ocupancy" )
        label_top_right = Gtk.Label(label="Battery Level")
        label_bottom_left = Gtk.Label(label="CPU Load")
        label_bottom_right = Gtk.Label(label="Available Bandwidth")
        
        #Simulations
        self.label_Simulation = Gtk.Label(label="Simulation")
        self.label_Buffer_Sim = Gtk.Label(label="Buffer is 0 %")
        self.label_Battery_state_Sim = Gtk.Label(label="Battery supply")
        self.label_Battery_Sim = Gtk.Label(label="Battery is 0 %")
        self.label_CPU_Sim = Gtk.Label(label="CPU is 0 %")
        self.label_BW_Sim = Gtk.Label(label="BW is 0 Kbs")
        
        #Enviorment
        self.label_Real = Gtk.Label(label="Enviorment")
        self.label_Buffer_Real = Gtk.Label(label="Buffer is 0 %") 
        self.label_Battery_Real = Gtk.Label(label="Battery is 0 %")
        self.label_CPU_Real = Gtk.Label(label="CPU is % ")
        self.label_BW_Real = Gtk.Label(label="BW is 0 Kbs")

        # in the grid:
        # attach the first label in the top left corner   (left_attach,right_attach,top_attach,bottom_attach)
        table.attach(hseparator_scenario, 0,4,0,1)
        table.attach(label_top_left,                0, 1, 1, 2)
        table.attach(label_top_right,               1, 2, 1, 2)
        table.attach(label_bottom_left,             0, 1, 4, 5)
        table.attach(label_bottom_right,            1, 2, 4, 5)
        
        table.attach(self.label_Simulation,         2, 3, 1, 2)        
        table.attach(self.label_Buffer_Sim,         2, 3, 2, 3)
        table.attach(self.label_Battery_Sim,        2, 3, 3, 4)
        table.attach(self.label_Battery_state_Sim,  2, 3, 4, 5)
        table.attach(self.label_CPU_Sim,            2, 3, 5, 6)
        table.attach(self.label_BW_Sim,             2, 3, 6, 7)
        
        table.attach(self.label_Real,               3, 4, 1, 2)        
        table.attach(self.label_Buffer_Real,        3, 4, 2, 3)
        table.attach(self.label_Battery_Real,       3, 4, 3, 4)
        table.attach(self.label_CPU_Real,           3, 4, 5, 6)
        table.attach(self.label_BW_Real,            3, 4, 6, 7)
        
        #Togle button Power supply
        PowerSupplyButton = Gtk.CheckButton(" Power Supply ")
        PowerSupplyButton.connect("toggled", self.on_button_power_supply, "1")
        table.attach (PowerSupplyButton, 1, 2, 2, 3)

        #Slider 1 Buffer
        self.Buffer_Sim = Gtk.HScale()
        self.Buffer_Sim.set_range(0, 100)
        self.Buffer_Sim.set_increments(1, 10)
        self.Buffer_Sim.set_digits(0)
        self.Buffer_Sim.set_size_request(50, 35)
        self.Buffer_Sim.connect("value-changed", self.BufferChange)
        table.attach(self.Buffer_Sim, 0, 1, 3, 4)
   
        #Slider 2
        self.CPU_Sim = Gtk.HScale()
        self.CPU_Sim.set_range(0, 100)
        self.CPU_Sim.set_increments(1, 10)
        self.CPU_Sim.set_digits(0)
        self.CPU_Sim.set_size_request(50, 35)
        self.CPU_Sim.connect("value-changed", self.CPUChange)
        table.attach(self.CPU_Sim, 0, 1, 5, 6)
         
        #Slider 3
        self.BW_Sim = Gtk.HScale()
        self.BW_Sim.set_range(0, 40000000)
        self.BW_Sim.set_increments(1, 10)
        self.BW_Sim.set_digits(0)
        self.BW_Sim.set_size_request(50, 35)
        self.BW_Sim.connect("value-changed", self.BWChange)
        table.attach(self.BW_Sim, 1, 2,5,6)
         
        #Slider 4
        self.Battery_Sim = Gtk.HScale()
        self.Battery_Sim.set_range(0, 100)
        self.Battery_Sim.set_increments(1, 10)
        self.Battery_Sim.set_digits(0)
        self.Battery_Sim.set_size_request(50, 35)
        self.Battery_Sim.connect("value-changed", self.BatteryChange)
        table.attach(self.Battery_Sim, 1, 2, 3, 4)
        
        self.entry = Gtk.Entry()#Cuadro de texto
        hbox.add(self.entry)
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
        
        #Control del Dashdemux por ahora
        #Selecciono ancho de Banda FALSE=BW_simulado TRUE=BW_Real
        self.dashdemuxer.set_property("dagomimux" , True)
        self.dashdemuxer.set_property("bw-source", False);
        
        #Variables que necesito inicializar al principio.
        self.dashdemuxer.set_property("system-battery-state", 0)
        self.dashdemuxer.set_property("system-battery-charge", 0)
        self.dashdemuxer.set_property("system-low-buffer", 0)
        self.dashdemuxer.set_property("system-cpu", 0)
        self.dashdemuxer.set_property("bw-sim", 0)

        
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)
        
    def open_mpd(self, w):
        #self.enviorment()
        if self.button_open.get_label() == "Play":
                self.player.set_state(Gst.State.PLAYING)
        #check button value 
        if self.button_open.get_label() == "Open":
            self.filepath = URLPRUEBAS
            #filepath = self.entry.get_text()
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
            print ("Enviorment Batt State")
            Battery = []
            Battery = self.enviormentBattery()
            self.dashdemuxer.set_property("system-battery-state", int(str(Battery[1])))
            self.label_Battery_Real.set_text("Battery is " + str(Battery[0]) + "%")
            self.dashdemuxer.set_property("system-battery-charge", int(str(Battery[0])))
        else:
            #print ("Simulation Batt State") 
            if button.get_active():
                state = "on"
                print("Button", name, "was turned", state)
                self.dashdemuxer.set_property("system-battery-state", 1)
                #self.label_Battery_state_Sim.set_text("Power supply")
                self.label_Battery_state_Sim.set_text("Battery state " + str(self.dashdemuxer.get_property("system-battery-state")))
                print ("Demux Battery state %s ") % self.dashdemuxer.get_property("system-battery-state")
                self.VARIABLE_ESTADO_BATERIA_TEMPORAL = 1
                #Text Overlay
                self.textoverlay.set_property("halignment", 0)
                self.textoverlay.set_property("valignment", 2)
                self.textoverlay.set_property("auto-resize", False)
                self.textoverlay.set_property("text", "prueeeeeeba")
                
            else:
                state = "off"
                print("Button", name, "was turned", state)
                self.dashdemuxer.set_property("system-battery-state", 0)
                #self.label_Battery_state_Sim.set_text("Battery supply")
                self.label_Battery_state_Sim.set_text("Battery state " + str(self.dashdemuxer.get_property("system-battery-state")))
                print ("Demux Battery state %s ") % self.dashdemuxer.get_property("system-battery-state")
                self.VARIABLE_ESTADO_BATERIA_TEMPORAL = 0
                self.textoverlay.set_property("halignment", 0)
                self.textoverlay.set_property("valignment", 2)
                self.textoverlay.set_property("auto-resize", False)
                self.textoverlay.set_property("text", "")
    def BatteryChange(self, event):
        if SELECTOR:
            print ("Enviorment Batt Level")
            Battery = []
            Battery = self.enviormentBattery()
            self.label_Battery_Real.set_text("Battery is " + str(Battery[1]) + "%")
            
            self.dashdemuxer.set_property("system-battery-charge", int(str(Battery[1])))
        else:
            #print ("Simulation Batt Level")
            #self.label_Battery_Sim.set_text("Battery is " + str(int(self.Battery_Sim.get_value())) + "%")
            self.label_Battery_Sim.set_text("Battery is " + str(int(self.dashdemuxer.get_property("system-battery-charge"))) + "%")
            self.dashdemuxer.set_property("system-battery-charge", int(self.Battery_Sim.get_value()))
    def BufferChange(self, event):
        if SELECTOR:
            print ("Enviorment Buffer (not implemented yet)")
        else:
            #print ("Simulation Buffer")
        
            '''
            0         Threshhold     100
            |------------|-----------|
                Danger        Optimal
             '''
            self.label_Buffer_Sim.set_text("Buffer is " + str(int(self.Buffer_Sim.get_value())) + "%")
            if int(self.Buffer_Sim.get_value()) <= BUFFERTHRESHOLD :
                self.dashdemuxer.set_property("system-low-buffer", 1)
            else :
                self.dashdemuxer.set_property("system-low-buffer", 0)
                
    def CPUChange(self, event):
        if SELECTOR:
            print ("Enviorment CPU Load ")
        else:
            #print ("Simulation CPU Load")
            self.label_CPU_Sim.set_text("CPU is " + str(int(self.CPU_Sim.get_value())) + "%" )
            self.dashdemuxer.set_property("system-cpu", int(self.CPU_Sim.get_value()))   

    def BWChange(self, event):
        
        self.label_BW_Sim.set_text("BW is " + str(int(self.BW_Sim.get_value())) + "Kbs")     
        self.dashdemuxer.set_property("bw-sim", int(self.BW_Sim.get_value()))   
        self.label_BW_Real.set_text("BW is" + str(self.dashdemuxer.get_property("bw-sim"))  + "Kbs")

    def enviormentBattery (self):
        BATT_NOW     =   "/sys/class/power_supply/BAT1/charge_now"
        BATT_FULL    =  "/sys/class/power_supply/BAT1/charge_full"
        BATT_STATUS  =     "/sys/class/power_supply/BAT1/status"    
    
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
        
    
    def readEnviorment (self):
        #falta definir el proceso de entorno completo para la seleccion SELECTOR = TRUE
        # de momento sacare el algoritmoa aqui
        Battery = []
        Battery = self.enviormentBattery()
        
        self.label_Battery_Real.set_text("Battery is " + str(Battery[0]) + "%")
        self.dashdemuxer.set_property("system-battery-charge", int(str(Battery[0])))

        threading.Timer(1.0, self.readEnviorment).start()
        cpuLoad = str( psutil.cpu_percent())
        #print "cpu %s" % prueb
        self.label_CPU_Real.set_text("CPU is " + str(cpuLoad) + "%")
        self.dashdemuxer.set_property("system-cpu", 0)

    def loadTemplateTile(self):
        ADAPTATIONSET = []
        BANDWITH = []
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
            BANDWITH.append(REPRESENTATIONATTRIB['bandwidth'])
        print BANDWITH
        
    def Algorithm (self):
        
        threading.Timer(2.0, self.Algorithm).start()
        print ("--- Algoritmo ---")
        #Fixed variables
        MAX_CPU     = 85
        MIN_BATT_LOAD   = 15
        VERY_LOW_BATT_LOAD = 5
        MIN_BUFFER      = 50
        
        #Enviorment (at the momenr only simulated conditions)
        SYSTEMCPU   = int(self.CPU_Sim.get_value())
        SYSTEM_BATTERY_STATE = self.VARIABLE_ESTADO_BATERIA_TEMPORAL
        SYSTEM_BATTERY_CHARGE = int(self.Battery_Sim.get_value())
        SYSTEM_BUFFER = int(self.Buffer_Sim.get_value())
        
        
        if SYSTEMCPU > MAX_CPU :
            print ("System CPU overload")
            #Calidad minima
        
        elif SYSTEMCPU <= MAX_CPU :
            print ("System CPU normal")
            #Uso normal del algoritmo
            
            #Check Battery
            if SYSTEM_BATTERY_STATE == 0: #Uso de la Bateria
                print ("uso bateria")
                if SYSTEM_BATTERY_CHARGE <= MIN_BATT_LOAD:
                    #usar textoverlay
                    print ("Bateria baja textoerlay")
                    if SYSTEM_BATTERY_CHARGE <= VERY_LOW_BATT_LOAD:
                        print ("calidad minima y textoverlay")
                    elif SYSTEM_BATTERY_CHARGE > VERY_LOW_BATT_LOAD:
                        #Rutina Buffer
                        if SYSTEM_BUFFER <= MIN_BUFFER :
                            print ("Buffer bajo")
                            #bajo una calidad
                        elif SYSTEM_BUFFER > MIN_BUFFER:
                            print ("Buffer OK")
                            #selecciono la mejor calidad seun el BW
                elif SYSTEM_BATTERY_CHARGE > MIN_BATT_LOAD:
                    print ("Bateria normal")
                                #Rutina Buffer
                    if SYSTEM_BUFFER <= MIN_BUFFER :
                        print ("Buffer bajo")
                        #bajo una calidad
                    elif SYSTEM_BUFFER > MIN_BUFFER:
                        print ("Buffer OK")
                        #selecciono la mejor calidad seun el BW
            elif SYSTEM_BATTERY_STATE == 1: #Uso del cargador
                print ("uso cargador")
                #Rutina Buffer
                if SYSTEM_BUFFER <= MIN_BUFFER :
                    print ("Buffer bajo")
                    #bajo una calidad
                elif SYSTEM_BUFFER > MIN_BUFFER:
                    print ("Buffer OK")
                    #selecciono la mejor calidad seun el BW    

if __name__ == "__main__":
    GObject.threads_init()
    GTK_Main()# run Python Class
    Gtk.main()# run Ui
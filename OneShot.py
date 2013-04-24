#!/usr/bin/env python

import pygtk
import __builtin__
import sys,os
import gtk
import gobject
from xml.etree import ElementTree

import linuxcnc
import hal
import gremlin
import gladevcp.makepins
from gladevcp.gladebuilder import GladeBuilder

# set up paths to files (in this case: /usr/bin/oneshot, usr/share/linuxcnc
BASE = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), ".."))
libdir = os.path.join(BASE, "lib", "python")
sys.path.insert(0, libdir)
datadir = os.path.join(BASE, "share", "linuxcnc")
gladeFile = os.path.join(datadir,"OneShot.glade")
feedSpeedFile = os.path.join(datadir,"feed-speed.xml")


class OneShot:


    def __init__(self):
        self.status = linuxcnc.stat()
        self.cmd = linuxcnc.command()
        self.err = linuxcnc.error_channel()
              
        self.builder = gtk.Builder()
        self.builder.add_from_file(gladeFile)
        self.halcomp = hal.component("oneshot")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window1") 
        self.error_statusbar = self.builder.get_object("statusbar_errors")
        self.status_statusbar = self.builder.get_object("statusbar_status")
        self.g92_led = self.builder.get_object("g92_led")
        self.estop_led = self.builder.get_object("estop_led")
        self.hal_meter_feed = self.builder.get_object("hal_meter_feed")
        self.window.show() 
        #self.window.maximize() 
        self.panel = gladevcp.makepins.GladePanel( self.halcomp, gladeFile, 
                                                   self.builder, None)
        self.halcomp.ready()
        gobject.timeout_add(500, self.periodic)
        
        self.loadFeedsAndSpeeds()
        self.addFeedsAndSpeeds()
        #self.createMaterialFilters()  
 
    def on_quit_action_activate(self, data=None):
        print "Quit menu clicked"
        gtk.main_quit()
  
    def on_face_settings_set_button_activate(self, button, data=None):
        self.sfmEntry.set_text("20000") 
        
    def on_stock_combobox_changed(self, combobox):
        print "on_stock_combobox_changed"
        #self.stockMaterialFilter.refilter()
        
    def on_tool_combobox_changed(self, combobox):
        print "on_tool_combobox_changed"
        #self.toolMaterialFilter.refilter() 
        
    def format_floats(self, column, cell, model, iter):
        idx = self.columnNames.index(column.get_title())
        cell.set_property('text', "%0.3f" % model.get_value(iter, idx))
    
    def filter_stock(self, model, iter, combobox):
        return model.get_value(iter,0) == combobox.get_active()
           
        
    def filter_tool(self, model, iter, combobox):
        return True
        
    def createMaterialFilters(self):
        self.stockMaterialFilter = self.feedSpeedStore.filter_new()
        self.toolMaterialFilter = self.feedSpeedStore.filter_new()
        self.stockMaterialFilter.set_visible_func(self.filter_stock,
                                                  self.stockCombobox)
        self.toolMaterialFilter.set_visible_func(self.filter_tool, 
                                                 self.toolCombobox)
    
    def loadFeedsAndSpeeds(self):
        """ Load machine speeds and feeds data from an XML file.
        
            Allows for a speeds and feeds table to be
            defined in an external file. The builtin getattr() method
            is necessary because XML only contains the "name" of 
            the types and values. (the word 'int', not an actual int())
        """
        self.stockMaterialList = list()
        self.toolMaterialList = list()
        treeRoot = ElementTree.parse(feedSpeedFile)
        cuttingDataList = treeRoot.getiterator(tag='cuttingData')
        self.columnType = [ getattr(__builtin__, col.get('type')) 
                            for col in cuttingDataList[0]]
        self.feedSpeedStore = gtk.ListStore(self.columnType[0], 
                                            self.columnType[1], 
                                            self.columnType[2], 
                                            self.columnType[3], 
                                            self.columnType[4])
        self.columnNames = [ col.tag for col in cuttingDataList[0]]
        
        for cuttingDataRow in cuttingDataList:
            r = list()
            for setting in cuttingDataRow:
                r.append(getattr(__builtin__,setting.get('type'))(setting.text))
                if setting.tag == 'stockMaterial':
                    if setting.text not in self.stockMaterialList:
                        self.stockMaterialList.append(setting.text)
                if setting.tag == 'toolMaterial':
                    if setting.text not in self.toolMaterialList:
                        self.toolMaterialList.append(setting.text)
            self.feedSpeedStore.append(r)
        
    def addFeedsAndSpeeds(self):
        self.stockCombobox = self.builder.get_object("stock_combobox")
        self.toolCombobox = self.builder.get_object("tool_combobox")
        self.feedSpeedView = self.builder.get_object("feedSpeedView")
        self.feedSpeedView.set_model(self.feedSpeedStore) 
        for col, name, coltype in zip(self.feedSpeedView.get_columns(), 
                                      self.columnNames, 
                                      self.columnType):
            col.set_title(name)
            if coltype == float:
                cell = gtk.CellRendererText()
                cell.set_property('xalign', 1.0)
                col.clear()
                col.pack_start(cell)
                col.set_cell_data_func(cell, self.format_floats)

        [self.stockCombobox.append_text(mat) for mat in self.stockMaterialList]
        self.stockCombobox.set_active(0)#glade bug fix?
        [self.toolCombobox.append_text(mat) for mat in self.toolMaterialList] 
        self.toolCombobox.set_active(0)#glade bug fix?   
        self.sfmEntry = self.builder.get_object("sfm_value")
        self.iptEntry = self.builder.get_object("ipt_value")
    
    def periodic(self):
        self.error_status = self.err.poll()
        if self.error_status:
            self.error_kind, self.error_text = self.error_status
            if self.error_kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                self.error_type = "Error: "
            else:
                self.error_type = "Info: "
            self.message_id = self.error_statusbar.push(0, self.error_type +
                                                      self.error_text) 
        self.status.poll()
        self.g92_led.hal_pin.set(sum(self.status.g92_offset))
        
        #if self.status.estop:
        #    self.estop_led.hal_pin.set(True)
        #else:
        #    self.estop_led.hal_pin.set(False)
        
        #print  "%0.3f" % self.status.feedrate
        self.hal_meter_feed.hal_pin.set(self.status.feedrate)
            
        return True #must return tru to keep running   
               
    
            
if __name__ == "__main__":
    instantiationInitializesAndCreates = OneShot()
    gtk.main()

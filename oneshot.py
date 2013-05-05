#!/usr/bin/env python

import pygtk
import __builtin__
import sys
import os
from os.path import expanduser
from exceptions import OSError, ValueError
from subprocess import check_call, CalledProcessError
import gtk
import gobject
from xml.etree import ElementTree

import linuxcnc
import hal
import gremlin

import gladevcp.makepins
import gladevcp.hal_actions
from gladevcp.gladebuilder import GladeBuilder

import time
import util

# set up paths to files (eg: /usr/bin, usr/share/linuxcnc)
configs = os.path.join(expanduser("~"), "linuxcnc", "configs", "Oneshot")
BASE = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), ".."))
libdir = os.path.join(BASE, "lib", "python")
sys.path.insert(0, libdir)
datadir = os.path.join(BASE, "share", "linuxcnc")
gladeFile = os.path.join(datadir, "oneshot.glade")
feedSpeedFile = os.path.join(datadir, "feed-speed.xml")


class OneShot:

    def __init__(self):
        self.status = linuxcnc.stat()
        self.cmd = linuxcnc.command()
        self.err = linuxcnc.error_channel()
        self.stockMaterialList = list()
        self.toolMaterialList = list()
        self.builder = gtk.Builder()
        self.builder.add_from_file(gladeFile)
        self.halcomp = hal.component("oneshot")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window1")
        self.error_statusbar = self.builder.get_object("statusbar_errors")
        self.status_statusbar = self.builder.get_object("statusbar_status")
        self.home_all_label = self.builder.get_object("home_all_label")
        self.g92_led = self.builder.get_object("g92_led")
        self.wcs_leds = tuple([self.builder.get_object("g5{0}_led".format(i))
                              for i in range(3, 9)])
        self.home_axes = {'home_x_button':0, 'home_y_button':1,
                     'home_z_button':2, 'home_all_button':-1}                            
        self.window.show()
        #self.window.maximize()
        self.panel = gladevcp.makepins.GladePanel(self.halcomp, gladeFile,
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
        print "on_stock_combobox_changed called"
        #self.stockMaterialFilter.refilter()
        
    def on_tool_combobox_changed(self, combobox):
        print "on_tool_combobox_changed called"
        #self.toolMaterialFilter.refilter() 

    def on_power_button_toggled(self, button):
        self.builder.get_object("homing_frame").set_sensitive(
                                button.get_active())
        self.builder.get_object("wcs_resets_frame").set_sensitive(
                                button.get_active())
    def printStatus(self, prefix=None):
        self.status.poll()
        if prefix:
            print prefix
        print "homed?: ", self.status.homed
        print "task_mode?:", self.status.task_mode
        #print prefix, "status.interp: ", self.status.interp_state
        #print prefix, "status.exec_state: ", self.status.exec_state
        #print prefix, "status.interp_state: ", self.status.interp_state
        #print prefix, "state: ", self.status.state
        #print prefix, "task_mode--------------: ", self.status.task_mode
        
    def on_home_button_toggled(self, button):
        
        #add mode and error checkin: must synchronize toggle states if error
        #gtk.Buildable.get_name solves glade ID glitch
        axisNum = self.home_axes[gtk.Buildable.get_name(button)]
        #if gladevcp.hal_actions.ensure_mode(self.status, self.cmd, 
        #        linuxcnc.MODE_MANUAL, linuxcnc.INTERP_IDLE):
               
        if button.get_active():
            if not util.ensure_mode(self.status, self.cmd, linuxcnc.MODE_MANUAL):
                state = util.interpStateNames[self.status.interp_state]
                mode = util.taskModeNames[self.status.motion_mode]
                secondary = " Current Status: {0} :: {1} ".format(state, mode)
                util.showErrorDialog("Unable to switch to MANUAL mode",
                                     secondary)
                return  #sync button status?                                    
            self.cmd.home(axisNum)
            self.status.poll()
            for i in range(10):
                time.sleep(1)
                self.status.poll()
                if (self.status.state == linuxcnc.RCS_DONE):
                    print "DONE" 
                    break
                if (self.status.state == linuxcnc.RCS_ERROR ):
                    util.showErrorDialog(self.err.poll()[1])
                    break
            
            
    
        else:
            self.cmd.unhome(axisNum) 
            self.printStatus()
            if axisNum == -1:  
                self.home_all_label.set_label('Home All') 
        
    def format_floats(self, column, cell, model, iter):
        idx = self.columnNames.index(column.get_title())
        cell.set_property('text', "%0.3f" % model.get_value(iter, idx))
    
    def filter_stock(self, model, iter, combobox):
        return model.get_value(iter, 0) == combobox.get_active()

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
        
        treeRoot = ElementTree.parse(feedSpeedFile)
        cuttingDataList = treeRoot.getiterator(tag='cuttingData')
        self.columnType = [getattr(__builtin__, col.get('type')) 
                            for col in cuttingDataList[0]]
        self.feedSpeedStore = gtk.ListStore(self.columnType[0], 
                                            self.columnType[1], 
                                            self.columnType[2], 
                                            self.columnType[3], 
                                            self.columnType[4])
        self.columnNames = [col.tag for col in cuttingDataList[0]]
        
        for cuttingDataRow in cuttingDataList:
            r = list()
            for setting in cuttingDataRow:
                r.append(getattr(__builtin__,
                                 setting.get('type'))(setting.text))
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
            if self.error_kind in (linuxcnc.NML_ERROR,
                                   linuxcnc.OPERATOR_ERROR):
                self.error_type = "Error: "
            else:
                self.error_type = "Info: "
            self.message_id = self.error_statusbar.push(0, self.error_type +
                                                      self.error_text) 
        self.status.poll()
        
        self.g92_led.hal_pin.set(sum(self.status.g92_offset))
        [led.set_active(False) for led in self.wcs_leds]
        self.wcs_leds[self.status.g5x_index].set_active(True)
        
        return True #must return tru to keep running   

    def get_handlers(halcomp, builder, useropts):
        print "%s.get_handlers() called" % (__name__)
        return [OneShot()]  


if __name__ == "__main__":
    instantiationInitializesAndCreates = OneShot()
    inifile = linuxcnc.ini(sys.argv[2])
    postgui_halfile = inifile.find("HAL", "POSTGUI_HALFILE")
    if postgui_halfile:
        print "postgui_halfile: ", postgui_halfile 
        try:
            check_call(["halcmd", "-f", os.path.join(configs, "postgui.hal")]) 
        except (OSError, ValueError, CalledProcessError) as e:
            print "Subprocessing Error: ", e.cmd    
            raise SystemExit(e.cmd)

    gtk.main()

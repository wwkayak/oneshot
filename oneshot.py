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


import linuxcnc
import hal
import gremlin

import gladevcp.makepins
import gladevcp.hal_actions
from gladevcp.gladebuilder import GladeBuilder

import time
import util
from errormanager import ErrorManager

# set up paths to files (eg: /usr/bin, usr/share/linuxcnc)
configs = os.path.join(expanduser("~"), "linuxcnc", "configs", "Oneshot")
BASE = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), ".."))
libdir = os.path.join(BASE, "lib", "python")
sys.path.insert(0, libdir)
datadir = os.path.join(BASE, "share", "linuxcnc")
gladeFile = os.path.join(datadir, "oneshot.glade")



class OneShot:

    def __init__(self):
        self.status = linuxcnc.stat()
        self.cmd = linuxcnc.command()
        self.err = linuxcnc.error_channel()
        self.errorDisplayTime = 0
        self.jogIncrement = .001
        self.errorQueueLen = int(inifile.find("DISPLAY", 
                                                "ERROR_QUEUE_LEN"))
        self.errorManager = ErrorManager(self.errorQueueLen)
        self.errorManager.connect("error_added", self.update_errors)
        self.notListening = False
        
        self.builder = gtk.Builder()
        self.builder.add_from_file(gladeFile)
        self.halcomp = hal.component("oneshot")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window1")
        self.error_label1 = self.builder.get_object("error_label1")
        self.error_label2 = self.builder.get_object("error_label2")
        self.home_all_label = self.builder.get_object("home_all_label")
        self.g92_led = self.builder.get_object("g92_led")
        self.mode_label = self.builder.get_object("mode_label")
        self.interp_label = self.builder.get_object("interp_label")
        self.exec_label = self.builder.get_object("exec_label")
        self.wcs_leds = tuple([self.builder.get_object("g5{0}_led".format(i))
                              for i in range(3, 9)])
        self.home_axes = {'home_x_button':0, 'home_y_button':1,
                     'home_z_button':2, 'home_all_button':-1} 
        self.errorWindow = self.builder.get_object("error_popup")
        self.errorWindowLabel = self.builder.get_object("error_queue_label") 
        #self.builder.get_object("spindle_adjustment").set_value(1.0)
        #self.feedAdjustment = self.builder.get_object("feed_adjustment")
        #self.feedAdjustment.set_value(100)                        
        self.window.show()
        self.window.maximize()
        self.panel = gladevcp.makepins.GladePanel(self.halcomp, gladeFile,
                                                   self.builder, None)
        self.halcomp.ready()
        gobject.timeout_add(500, self.periodic)
    
    def update_errors(self, errorMngr):
        error = errorMngr.getLastError()
        self.error_label2.set_text(self.error_label1.get_text())
        self.error_label1.set_text( error[0] + error[1] + error[2] )
 
    def on_quit_action_activate(self, data=None):
        print "Quit menu clicked"
        gtk.main_quit()
    
    def on_error_statusbar_enter_notify_event(self, statusbar, event):
        errs = self.errorManager.getErrors()
        if not errs: 
            return
        errTxt = ["{0}-{1}{2}".format(err[0], err[1], err[2]) for err in errs]
        self.errorWindowLabel.set_text('\n'.join(errTxt))
        self.errorWindow.show()
        self.errorWindow.present()
 
    def on_error_statusbar_leave_notify_event(self, statusbar, event): 
        self.errorWindow.hide()  
    
    def on_feed_minus_button_clicked(self, button):
        self.feedAdjustment.set_value(self.feedAdjustment.get_value()-1)
        
    def on_feed_plus_button_clicked(self, button):
        self.feedAdjustment.set_value(self.feedAdjustment.get_value()+1)        
       
       
    def on_g28_1_button_clicked(self, button):
        if util.ensure_mode(self.status, self.cmd, linuxcnc.MODE_MDI):
            self.cmd.mdi("G28.1")
            print "G28.1 succeeded"
        else:
            print "G28.1 failed?"
            
    def on_g28_button_clicked(self,  button):
        if util.ensure_mode(self.status, self.cmd, linuxcnc.MODE_MDI):
            self.cmd.mdi("G28 Z2")
            self.cmd.wait_complete()             

    def on_status_pop_button_released(self, button):  #?????????????????
        self.error_statusbar.pop(self.context_id)
    
    def on_face_settings_set_button_activate(self, button, data=None):
        self.sfmEntry.set_text("20000")

    def on_stock_combobox_changed(self, combobox):
        print "on_stock_combobox_changed called"
        #self.stockMaterialFilter.refilter()
        
    def on_tool_combobox_changed(self, combobox):
        print "on_tool_combobox_changed called"
        #self.toolMaterialFilter.refilter() 
        
    def on_jog_x_plus_pressed(self, button):
        print "x+ pressed@{0}".format(self.jogIncrement)
        self.cmd.jog(linuxcnc.JOG_CONTINUOUS, 0, self.builder.get_object("jog_speed").get_value())
        
    def on_jog_x_plus_released(self, button):
        print "x+ released@{0}".format(self.jogIncrement)
        self.cmd.jog(linuxcnc.JOG_STOP, 0)
    
    def on_jog_x_minus_pressed(self, button):
        print "x- pressed@{0}".format(self.jogIncrement)
    
    def on_jog_x_minus_released(self, button):
        print "x- released@{0}".format(self.jogIncrement)
    
    def on_jog_y_plus_pressed(self, button):
        print "y+ pressed@{0}".format(self.jogIncrement)
    
    def on_jog_y_plus_released(self, button):
        print "y+ released@{0}".format(self.jogIncrement)
    
    def on_jog_y_minus_pressed(self, button):
        print "y- pressed@{0}".format(self.jogIncrement)
    
    def on_jog_y_minus_released(self, button):
        print "y- released@{0}".format(self.jogIncrement)
    
    def on_jog_z_plus_pressed(self, button):
        print "z+ pressed@{0}".format(self.jogIncrement)
    
    def on_jog_z_plus_released(self, button):
        print "z+ released@{0}".format(self.jogIncrement)
    
    def on_jog_z_minus_pressed(self, button):
        print "z- pressed@{0}".format(self.jogIncrement)
    
    def on_jog_z_minus_released(self, button):
        print "z- released@{0}".format(self.jogIncrement)
    
    def on_jog_speed_button_toggled(self, button):
        if self.notListening: 
            return
        self.notListening = True
        self.builder.get_object("jog_slow_button").set_active(False)
        self.builder.get_object("jog_med_button").set_active(False)
        self.builder.get_object("jog_fast_button").set_active(False)
        button.set_active(True)
        self.jogIncrement = float(button.get_label())
        print "jogIncrement", self.jogIncrement
        self.notListening = False
    
    def on_power_button_toggled(self, button):
        self.builder.get_object("homing_frame").set_sensitive(
                                button.get_active())
        self.builder.get_object("wcs_resets_frame").set_sensitive(
                                button.get_active())
            
    def on_home_button_toggled(self, button):
        axisNum = self.home_axes[gtk.Buildable.get_name(button)]#glade glitch
        if button.get_active():
            if not util.ensure_mode(self.status, self.cmd, linuxcnc.MODE_MANUAL):
                util.showErrorDialog("Unable to switch to manual mode!")
                self.synchronizeToggleButtons()
                return  #sync button stati?                                    
            self.cmd.home(axisNum)
            self.status.poll()
            for waitToComplete in range(1):
                time.sleep(.1)
                self.status.poll()
                if self.status.state is linuxcnc.RCS_DONE:
                    self.home_all_label.set_label('Un-home All')
                    break
                if self.status.state is linuxcnc.RCS_ERROR:
                    util.showErrorDialog("RCS_ERROR", self.err.poll()[1])
                    break
            self.synchronizeToggleButtons()
        else:
            if not util.ensure_mode(self.status, self.cmd, linuxcnc.MODE_MANUAL):
                util.showErrorDialog("Unable to switch to manual mode!")
                self.synchronizeToggleButtons()
            self.cmd.unhome(axisNum) 
            if axisNum == -1:  
                self.home_all_label.set_label('Home All') 
            self.synchronizeToggleButtons()
    
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
    def synchronizeToggleButtons(self):
        self.status.poll()
        print "homed............", self.status.homed    
    
    def periodic(self):
        self.status.poll()
        self.mode_label.set_text(util.taskModeNames[self.status.task_mode])
        self.interp_label.set_text(
                             util.interpStateNames[self.status.interp_state])
        self.exec_label.set_text(util.execStateNames[self.status.exec_state])
        self.g92_led.hal_pin.set(sum(self.status.g92_offset))
        [led.set_active(False) for led in self.wcs_leds]
        self.wcs_leds[self.status.g5x_index].set_active(True)
        return True #must return tru to keep running   
   
    def get_handlers(halcomp, builder, useropts):
        print "%s.get_handlers() called" % (__name__)
        return [OneShot()]  


if __name__ == "__main__":
    inifile = linuxcnc.ini(sys.argv[2])
    postgui_halfile = inifile.find("HAL", "POSTGUI_HALFILE")
    instantiationInitializesAndCreates = OneShot()
    if postgui_halfile:
        try:
            check_call(["halcmd", "-f", os.path.join(configs, postgui_halfile)]) 
        except (OSError, ValueError, CalledProcessError) as e:
            print "Subprocessing Error: ", e.cmd    
            raise SystemExit(e.cmd)

    gtk.main()

import gtk
import linuxcnc


taskModeNames = {linuxcnc.MODE_MANUAL : "MANUAL",
                 linuxcnc.MODE_AUTO : "AUTO",
                 linuxcnc.MODE_MDI : "MDI" }
                      
interpStateNames = {linuxcnc.INTERP_IDLE : "IDLE",
                    linuxcnc.INTERP_READING : "READING",
                    linuxcnc.INTERP_PAUSED : "PAUSED",
                    linuxcnc.INTERP_WAITING : "WAITING" } 
                     
execStateNames = {linuxcnc.EXEC_ERROR : "ERROR",
                  linuxcnc.EXEC_DONE : "DONE",
                  linuxcnc.EXEC_WAITING_FOR_MOTION : "WAITING_FOR_MOTION",
                  linuxcnc.EXEC_WAITING_FOR_MOTION_QUEUE : 
                                                    "WAITING_FOR_MOTION_QUEUE",
                  linuxcnc.EXEC_WAITING_FOR_PAUSE : "WAITING_FOR_PAUSE",
                  linuxcnc.EXEC_WAITING_FOR_MOTION_AND_IO : 
                                                   "WAITING_FOR_MOTION_AND_IO",
                  linuxcnc.EXEC_WAITING_FOR_DELAY : "WAITING_FOR_DELAY",
                  linuxcnc.EXEC_WAITING_FOR_SYSTEM_CMD : 
                                                      "WAITING_FOR_SYSTEM_CMD"}
                                                          
                  
def showMessageDialog(message):
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
                               gtk.BUTTONS_OK, message)
    dialog.run()
    dialog.destroy() 
        
def showWarningDialog(message):
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, 
                               gtk.BUTTONS_YES_NO, message)
    choice = dialog.run()
    dialog.destroy()
    return choice == gtk.RESPONSE_YES                               

def showErrorDialog( message=None, secondaryText=None):
    if message is None:
        message = "Error!" 
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                               gtk.BUTTONS_OK, message)
    if secondaryText is None:
        state = interpStateNames[self.status.interp_state]
        mode = taskModeNames[self.status.motion_mode]
        secondaryText = " Current Status: {0} :: {1} ".format(state, mode)
    dialog.format_secondary_text(secondaryText)
    dialog.run()
    dialog.destroy() 

def interpIdle(status, do_poll=True):
    if do_poll: 
        s.poll()
    return status.interp_state == linuxcnc.INTERP_IDLE    
        
def ensure_mode(status, command, *modes):
    status.poll()
    if not modes: 
        return False
    if status.task_mode in modes: 
        return True
    if not interpIdle(status, do_poll=False): 
        return False
    command.mode(modes[0])
    command.wait_complete()
    return True   

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
                             

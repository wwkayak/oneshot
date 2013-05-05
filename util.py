import gtk
import linuxcnc

taskModeNames = {linuxcnc.MODE_MANUAL : "MODE_MANUAL",
                 linuxcnc.MODE_AUTO : "MODE_AUTO",
                 linuxcnc.MODE_MDI : "MODE_MDI" }
                      
interpStateNames = {linuxcnc.INTERP_IDLE : "INTERP_IDLE",
                    linuxcnc.INTERP_READING : "INTERP_READING",
                    linuxcnc.INTERP_PAUSED : "INTERP_PAUSED",
                    linuxcnc.INTERP_WAITING : "INTERP_WAITING" }                      
                  
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

def showErrorDialog( message, secondaryText=None):
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                               gtk.BUTTONS_OK, message)
    if secondaryText != None:
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
        
                             

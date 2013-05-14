import gtk
import linuxcnc
import gobject
from time import gmtime, strftime

class ErrorManager(gobject.GObject):
   
   def __init__(self, errorQueueLen=None):
      self.__gobject_init__()
      self.err = linuxcnc.error_channel()
      self.errorQueue = list()
      if errorQueueLen:
         self.queueLenMax = errorQueueLen
      else:
         self.queueLenMax = 3     
      gobject.timeout_add(100, self.pollErrors)
     
   def push(self, error):
      if len(self.errorQueue) >= self.queueLenMax:
         self.errorQueue.pop()
      self.errorQueue.append(error)
      self.emit('error_added')
   
   def pop(self):
      return self.errorQueue.pop()
   
   def getLastError(self):
      return self.errorQueue[-1]
    
   def getErrors(self):
      if len(self.errorQueue): 
         return reversed(self.errorQueue[:])
      else:
         return None
     
   def pollErrors(self):
        error = self.err.poll()
        if error:
            error_kind, error_text = error
            if error_kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                error_type = "Error :: "
            else:
                error_type = "Info :: "
            errTime = strftime("%I:%M:%S :: ",gmtime())
            self.push((errTime, error_type, error_text))
        return True
        
gobject.type_register(ErrorManager) 
gobject.signal_new('error_added', ErrorManager, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())



 

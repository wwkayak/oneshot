import gtk
import linuxcnc
import gobject

class ErrorManager(gobject.GObject):
   
    
   def __init__(self, errorQueueLen=None):
      self.__gobject_init__()
      self.errorQueue = list()
      if errorQueueLen:
         self.queueLenMax = errorQueueLen
      else:
         self.queueLenMax = 3     

   def push(self, error):
      if len(self.errorQueue) >= self.queueLenMax:
         self.errorQueue.pop()
      self.errorQueue.append(error)
      self.emit('model_changed')
   
   def pop(self):
      return self.errorQueue.pop()
   
   def getLastError(self):
      return self.errorQueue[-1]
    
   def getErrors(self):
      s = list()
      
      for e in self.errorQueue:
         s.append(e)
      return '\n'.join(s)

gobject.type_register(ErrorManager) 
gobject.signal_new('model_changed', ErrorManager, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())



 

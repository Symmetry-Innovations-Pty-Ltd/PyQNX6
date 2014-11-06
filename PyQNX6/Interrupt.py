#!/usr/bin/python

#import pdb
import sys, os

from ctypes import *

from PyQNX6 import *

	
#####################################################




class Interrupt (QNX):
    """
    Interrupt class.
    Encapsulates the methods related to QNX Interrupt handling. 
    NB Assumes an interrupt per class instance
    Functions: 
	    - InteruptAttachEvent (Irq, Event, Flags = _NTO_INTR_FLAGS_TRK_MSK)
	    - InterruptWait (Flags = 0, Timeout = None)
	    - InterruptUnmask ()
	    - InterruptMask  ()
	    - InterruptDetach ()
	    - InterruptFunction (Fn)
   
    For more information on the Events See PyQNX6.core 
    """

    _NTO_INTR_FLAGS_TRK_MSK = 8  
    _NTO_INTR_FLAGS_PROCESS = 4
    _NTO_INTR_FLAGS_END     = 1

    def __init__ (self, Irq = None, Event = None):
	"""
	Instantiates the Interrupt class. 
	Creates the ctypes function links.
	Calls ThreadCtl to allow privilaged instructions. 
	If created with an Irq and Event, saves the parameters for
	a future InterruptAttachEvent.

	@param Irq: The interrupt number 0=timer, 3,4=seral etc. 
	@param Event: The event that will be triggered when the interrupt occurs.

	The interupt and the event may be specified at instantiation but wont be
	activated until later.  

	"""
	if QNX.lib == None:
	    QNX.__init__(self)    # init libc
	self._InterruptAttachEvent = self.lib.InterruptAttachEvent
	self._InterruptAttachEvent.argtypes = [c_int, POINTER (sigevent), c_int]
	self._InterruptWait = self.lib.InterruptWait
	self._InterruptWait.argtypes = [c_int, c_char_p]
	self._InterruptUnmask = self.lib.InterruptUnmask
	self._InterruptMask = self.lib.InterruptMask
	self._InterruptDetach = self.lib.InterruptDetach

	self.lib.ThreadCtl (1, 0)
	self.Id    = -1
	self.Irq   = Irq
	self.Event = Event
	self.Flags = self._NTO_INTR_FLAGS_TRK_MSK

	
    def InterruptAttachEvent (self, Irq = None, Event = None, \
				Flags = _NTO_INTR_FLAGS_TRK_MSK):
	"""
	Method to attach to an event to an interrupt. 
	The Event will define the action to be taken when an interrupt occurs
	By default we track the mask count. 

	@param Irq: The hardware interrupt to attach to. If None use the one that was defined at instantiation. 
	@param Event: The event to trigger. If None, see Irq. 
	@return the Id of the attachment.

	If this instance is already attached. We Unmask, Detach and re-Attach. 
    
	"""
	if not Irq is None:   self.Irq   = Irq
	if not Event is None: self.Event = Event
	self.Flags = Flags

	assert self.Irq != None, "No Irq defined"

	if self.Id != -1:  		# are we already attached?
            self.InterruptUnmask ()	# unmask
            self.InterruptDetach ()    	# detach
	self.Id = self._InterruptAttachEvent (self.Irq, pointer(self.Event), 
	                                      self.Flags)
	return self.Id
    
    def InterruptUnmask (self):
	"""
	InterruptUnmask. Unkasks the current interrupt. 
	@return The result of InterruptUnmask. See QNX docs.
	"""
	Result = self._InterruptUnmask (self.Irq, self.Id)
	return Result

    def InterruptMask (self):
	"""
	InterruptMask. Masks the specified interrupt
	Calls InterruptUnmask with the current Irq and Id. 
	@return The result of InterruptMask. See QNX docs.
	"""
	Result = self._InterruptMask (self.Irq, self.Id)
	return Result
    
    def InterruptWait (self):
	# (WaitFlags = 0, Timeout = None):
	"""
	InterruptWait. Blocks the caller, Waits to be unblocked by an interrupt.
	The Event provided at InterruptAttachEvent will have been EVT_INTR.
	
	@return The result of the InterruptWait call. See QNX docs.
	"""	
	Result = self._InterruptWait (0, None)
	return Result
    
    def InterruptDetach (self):
	"""
	InterruptDetach. Detach from the attached interrupt identified by 'Id'.

	@return The result of the InterruptDetach call. See QNX docs.
	Also sets the instance Id to -1. 
	"""
	Result = self._InterruptDetach (self.Id)
	self.Id = -1  # indicates done/free/unused
	return Result
    

    def InterruptFunction (self, Fn, Irq=None):
	"""
	InterruptFunction. A general utility function, to facilitate using interrupts.
	
	@param Fn: The function to call once the interrupt has fired. 
	@param Irq: The interrupt to attach to. If not supplied - use the instance Irq. 
	@return 0 if exited sucessfully else -1 if error in Fn.
	
	Attaches to an interrupt, blocks until an interrupt then - 
	- Unmasks
	- Calls the handler function.
	- Returns to being blocked.  
	
	If an error occurs the interrupt is unmasked and detached and the InterruptFunction returns.
	Also if the function returns True then the while loop exits  
	

	"""
	def _DoCleanup():
	    self.InterruptUnmask ()  # Done, so clean up - unmask
	    self.InterruptDetach ()  # and detach

	if Irq == None: Irq = self.Irq
	self.Event = sigevent (SIGEV_INTR)
	self.Id = self.InterruptAttachEvent (Irq, self.Event)

	Continue = True
	while Continue:
	    try: 
		self.InterruptWait ()    # wait for the interrupt
	    except: 
		Continue = False
		continue

	    self.InterruptUnmask ()      # clean up the mask
	    try:
		Result = Fn ()		# call the fucntion
	 	if Result == True:	# if we get a true then stop 
	    	    Continue = False
		    _DoCleanup ()
	    except: 
		Continue = False
		_DoCleanup ()
		print "PyQNX6.Interrupt: Error in called InterruptFunction. Exiting"
		return -1
	return 0
		


if __name__ == '__main__':
    
    a = 0
    count = 1
    def Test ():
	global a, count

	count -= 1
	if count == 0:
	    count = 1000
	    sys.stdout.write ("%d " % (a))
	    sys.stdout.flush()
	    a +=1
	return False
	
    I = Interrupt (Irq=0)

    I.InterruptFunction (Test)
	
    
    

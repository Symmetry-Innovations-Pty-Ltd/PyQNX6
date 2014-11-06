#!/usr/local/bin/python

#import pdb
import sys, os

from PyQNX6    import *
from ctypes import *

__version__ = "0.1"

class Timer (QNX):
    """
    Timer Class.
    Encapsulates the QNX methods related to Timer management functions. 
    
    - __init__      (Event = None, Times = None, Abs = False, Start=False)
    - timer_create  (Sigevent= None)
    - timer_settime (Abs = None, Itime = None)
    - timer_stop    ()
    - timer_delete  ()
    """

    def __init__ (self, Event = None, Times = None, Abs = False, Start = False):
	"""
	@param Event: The sigevent to be fired when teh timer expires
	@param Times: Definition of timer expiry and re-triggering. (tuple)
	@param Abs:   Absolute or Relative timer.
	@type Abs: boolean
	@param Start: Start the timer now. 
	@type Start: boolean
	Stores the parameters. If Start is true - creates and starts the timer
	"""
	if QNX.lib == None:
	    QNX.__init__(self)    # init libc
	self._timer_create = self.lib.timer_create
	self._timer_create.argtypes = [c_int, POINTER(sigevent), POINTER(c_int)]
	self._timer_settime = self.lib.timer_settime
	self._timer_settime.argtypes = [c_int, c_int, POINTER(itimerspec), POINTER (itimerspec)]
	self._timer_delete = self.lib.timer_delete
	
	self.Id    = None
	self.Event = Event
	self.Times = Times
	self.Abs   = Abs
	if (Start):      # assume all parameters are in place. If not the function will reject.
	    self.timer_create ()
	    self.timer_settime ()
		

    def timer_create (self, Sigevent= None):
	"""
	timer_create. Creates a Timer and initialises it with the instance sigevent or the one provided. 
	Creates the timer. 
	@param Sigevent: Event to be attached to the timer. 
	if no sigevent is found then a ValueError is raised.
	@return: The result of timer_create. See the QNX docs.
	"""
	_Id = c_int (0)
	if Sigevent: self.Event = Sigevent
	if self.Event == None: raise ValueError, "No Event defined"
	_res = self._timer_create (0, pointer (self.Event) , pointer (_Id))
	self.Id = _Id.value
	return _res

    def timer_delete (self):
	"""
	timer_delete. Deletes the instance timer.
	@return: The result of the timer_dlete call. see QNX docs. 
	"""
	return self._timer_delete (self.Id)

    def timer_settime (self, Abs = None, Times = None):
	"""
	timer_settime. Sets the instance timer. 
	@param Abs: The itime time is Absolute or Relative. 
	@param Times: Defines start and repeat intervals. (tuple)
	@return: The result of the timer_settime call. See QNX docs. 
	If no Itime value can be found - we raise a ValueError exception. 
	"""
	if Abs:   self.Abs   = Abs
	if Times: self.Times = Times
	if self.Times == None: raise ValueError, "No Start/Interval time defined"
	Itime = itimerspec (self.Times[0], self.Times [1])
	_res =  self._timer_settime (c_int(self.Id), c_int(self.Abs), pointer (Itime), None)
	return _res

    def timer_stop (self):
	"""
	timer_stop. Stops the instance timer. 
	Calls timer_settime with am itimespec of zeroes.
	@return the result of the timer-settime call. See QNX docs. 
	"""
	return self.timer_settime (0, (0, 0))
	


if __name__ == '__main__':
    t = Timer ()
    print dir (t)
    

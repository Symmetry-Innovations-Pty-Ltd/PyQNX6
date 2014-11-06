#!/usr/bin/python
"""
Symmetry Innovations Pty Ltd. admin@symmetry.com.au

QNX core classes/data

"""
#import pdb
import sys, os, time

from ctypes import *


class QNX(object):
    """
    QNX Class Placeholder for the functions in libc.
    """
    lib = None
    def __init__ (self, libname="libc.so"):
	"""
	Initialise the class. If the library isnt already loaded then load the library.
	"""
	if QNX.lib == None:
		QNX.lib = self.lib = cdll.LoadLibrary (libname)
	    #self.get_errno_loc = self.lib.errno
	    #self.get_errno_loc.restype = c_int


class sigval_u (Union):
    """
    Wrapper for the sigval union. 
    """
    _fields_ = [('sival_int', c_int32),
                ('sival_ptr', c_void_p)]
    
    def __repr__ (self):
	return "<sigval int %d>" % (self.sival_int)
    
    
class pulse_t  (Structure):
    """
    Wrapper for the QNX pulse_t structure. 
    """
    # size verified.
    _fields_ = [('type', c_int16), 
		('subtype', c_int16),
		('code', c_int8),
		('zero', c_int8*3),
		('sigval', sigval_u),
		('scoid', c_int32)]
    def __repr__ (self):
	"""
	String representation of pulse_t instances. 
	"""
	return "<pulse %d,%d>" % (self.code, self.sigval.sival_int) 

    def __len__ (self):
	return sizeof (self)

    def Copy (self):
	Result = pulse_t()
	Result.type = self.type
	Result.subtype = self.subtype
	Result.code = self.code
	Result.sigval = self.sigval
	Result.scoid  = self.scoid
	return Result

# definition for the name_attach_t structure
class name_attach_t (Structure):
    """
    Name attach data structure. 
    Used by QNX connect and process naming functions
    Mostly needed for 'chid'.
    """
    _fields_ = [("dpp", c_void_p), # int),
                ("chid", c_int),
		("mntid", c_int),
		('zero1', c_int), ('zero2', c_int)]

class msg_info_t (Structure):
    """
    msg_info structure. 
    Returned by MsgReceive to give more informaton about the caller and the message
    """
    _fields_ = [("nd", c_int), 
                ("srcnd", c_int),
                ("pid", c_int),
		("tid", c_int),
		("chid", c_int),
		("scoid", c_int),
		("coid", c_int),
		("msglen", c_int),
		("srcmsglen", c_int),
		("dstmsglen", c_int),
		# 16 bits 
		("priority", c_int16), ("flags", c_int16),
		("reserved", c_uint32)]


#########################

SIGEV_PULSE   = 4 #: sigev_notify type - notify via a pulse.
SIGEV_UNBLOCK = 5 #: sigev_notify type - cause an unblock
SIGEV_INTR    = 6 #: sigev_notify type - unblock form an interrupt

class sigevent (Structure):
    """
    sigevent structure.
    Used by interrupts, timers, MsgDeliver. 
    Most event driven activities.
    There are 3 supported events. 
    Intr(), Unblock() and Pulse() are support methods that initialise this structure. 

    """
    _fields_ = [('sigev_notify', c_int),
                ('sigev_coid', c_int),
		('sigev_value', c_int),
		('sigev_code', c_short),
		('sigev_priority', c_short)]

    def __init__ (self, notify = None, priority = 10, \
			code = 0, value= 0, coid=0):
	"""
	sigevent. Initialise the instance. 
	Intiialisation is done according to 'notify'
	Supported types are :
	    SIGEV_PULSE
	    SIGEV_UNBLOCK
	    SIGEV_INTR 

	Initialising methods exist also, NB they return self.
	"""
	Structure.__init__(self)

	if notify == SIGEV_INTR:  self.Intr()
	elif notify == SIGEV_UNBLOCK: self.Unblock()
	elif notify == SIGEV_PULSE: 
	    self.Pulse (coid, priority, code, value)
    
    def __repr__ (self):
	"""
	String representation of sigevent_t instances. 
	"""
	notify = self.sigev_notify	
        if notify == SIGEV_INTR:
	   return "<intr >"  
	elif notify == SIGEV_UNBLOCK:
	   return "<unblock >" 
	elif notify == SIGEV_PULSE: 
	   return "<pulse %d,%d>" % (self.sigev_code, self.sigev_value) 
        else: 
	   return "<undef >"

	
    def Intr (self):
	"""
	Initialise this class for notifying an interrupt
	"""
	self.sigev_notify = SIGEV_INTR    # from sys/siginfo.h
	return self

    def Unblock (self):
	"""
	Initialise this class for unblocking
	"""
	self.sigev_notify = SIGEV_UNBLOCK
	return self
    
    def Pulse (self, coid=0, priority = 10, code = 0, value=0 ):
	"""
	Initialise this class for delivering a pulse
	"""
	self.sigev_notify   = SIGEV_PULSE
	self.sigev_coid     = coid
	self.sigev_priority = priority
	self.sigev_code     = code
	self.sigev_value    = value
	return self

def Waitfor (Name):
    """
    Utility: Wait for the file Name to exist. 
    Will wait for the existance of the named file. 

    This is similar in functionality to the QNX 'waitfor' utility.
    It does not have a timeout option.
    """
    __waitfor = True
    while __waitfor:
	try:
	    f = open (Name, "r")
	    __waitfor = False
	    f.close()
	except: 
	    time.sleep (0.1)

def WaitforAttach (Name, Global = False):
    """
    Utility: Waitfor the attached name to exist.
    Will wait for the existance of the named attach file. 
    This may be used after name_attach call to force the code to wait until
    the name has been registered. 
    """

    if Global:  Name = "/dev/name/global/" + Name
    else:  Name = "/dev/name/local/" + Name
    Waitfor (Name)
	
	
#######################################################
#
# timer related classes
#

class timespec (Structure):
    """
    timespec: structure matching the POSIX.
    Defines seconds and nano seconds. 
    """
    _fields_ = [("tv_sec", c_uint32),
                ("tv_nsec", c_uint32)]
		
    def __repr__ (self):
	return "<timespec %dSec, %dnSec>" % (self.tv_sec, self.tv_nsec)
    
import math 

class itimerspec (Structure):
    """
    itimerspec: structure matching the POSIX.
    Holds two timespec structures.
    """
    _fields_ = [("it_value", timespec),
                ("it_interval", timespec)]

    def __init__(self, #val_sec=0, val_nsec=0, inter_sec=0, inter_nsec=0,
	Start, Repeat):
	"""
	Initialise the itimerspec structure.
	"""
	Structure.__init__(self)
	if True : #Start and Repeat: 
	    self.Set (Start, Repeat)
	else: 
	    self.it_value.tv_sec     = 0 #val_sec
	    self.it_value.tv_nsec    = 0 #val_nsec
	    self.it_interval.tv_sec  = 0 #inter_sec
	    self.it_interval.tv_nsec = 0 #inter_nsec

    def __repr__ (self):
	"""
	String representation of this itimerspec instance.
	"""
	return "<itimerspec: %d,%d %d,%d>" %  \
                    (self.it_value.tv_sec, self.it_value.tv_nsec, \
                    self.it_interval.tv_sec, self.it_interval.tv_nsec)
    
    def Set (self, Start, Repeat ): #val_sec=0, val_nsec=0, inter_sec=0, inter_nsec=0):
	"""
	Initialise the itimerspec data.
	Params: Start, Repeat - float seconds.
	"""
	self.it_value.tv_sec     = int (Start)
	self.it_value.tv_nsec    = self.S2nS (math.modf (Start) [0])
	self.it_interval.tv_sec  = int (Repeat)
	self.it_interval.tv_nsec = self.S2nS (math.modf (Repeat) [0])
	# old
	#self.it_value.tv_sec  = val_sec
	#self.it_value.tv_nsec = val_nsec
	#self.it_interval.tv_sec  = inter_sec
	#self.it_interval.tv_nsec = inter_nsec


    def MS2nS (self, MilliSeconds):
	"""
	Helper / Utility method. Used to convert Milliseconds to nanoSeconds.
	nano Seconds are used extensively in this structure. 
	"""
	return int (MilliSeconds *1000000)

    def S2nS (self, Seconds):
	"""
	Helper / Utility method. Used to convert Milliseconds to nanoSeconds.
	nano Seconds are used extensively in this structure. 
	"""
	return int (Seconds *1000000000)
	

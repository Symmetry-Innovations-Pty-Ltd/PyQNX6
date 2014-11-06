#!/usr/bin/python
"""
QNX Resource Manager interface.
Provides class implimentations of the major QNX structures (via ctypes).
Also a Resmgr class to enable users to define their own Resmgr methods. These 
will be called to handle specific io_open and io_connect functions. 

The attributes and ocb structures are automatically handled by the class. Extending 
attributes and ocbs can be done using the pythn classes. There are exanmples.  

"""

#import pdb

from ctypes import *
from PyQNX6 import (QNX, Structure, msg_info_t, pulse_t )
from PyQNX6.Message import Message #*

import time, sys, os

__version__ = 'v0.2'
__author__ = 'andy.rhind@symmetry.com.au'



class resmgr_attr_t (Structure):
    """
    Resource Manager attributes structure.
    The structure is initialised to Flags=0, nparts_max=1, msg_max_size=4096
    """
    # size verified
    _fields_ = [('flags', c_uint),
                ('nparts_max', c_uint),
		('msg_max_size', c_uint),
		('other_func', c_void_p),
		('reserved', c_uint*4)
		]

    def __init__(self, Nparts=1, MsgMaxSize=4096, Flags = 0):
	self.flags = Flags
	self.nparts_max = Nparts
	self.msg_max_size = MsgMaxSize
	self.other_func = None


class iovec (Structure):
    """
    QNX - iovec structure. 
    """
    _fields_ = [('iov_base', c_void_p),
                ('iov_len', c_int)]


""" 
QNX - POSIX message structures
"""

class io_open_t (Structure):
    """
    io_open_t 
    Describes the message received for open/connect calls. 
    The resmgr handler replies with the status. 
    """
    # size verified
    _fields_ = [('type', c_uint16),
		('subtype', c_uint16),
		('file_type', c_uint32),
		('reply_max', c_uint16),
		('entry_max', c_uint16),
		('key', c_uint32),
		('handle', c_uint32),
		('io_flag', c_uint32),
		('mode', c_uint32),
		('sflag', c_uint16),
		('access', c_uint16),
		('zero', c_uint16),
		('path_len', c_uint16),
		('eflag', c_uint8),
		('extra_type', c_uint8),
		('extra_len', c_uint16),
		('path',    c_char)
               ]


class io_write_t (Structure):
    """
    io_write_t
    Describes the message received for write () requests.
    The resmgr handler replies with, no data and the number of bytes written, or error
    """
    _fields_ = [('type', c_uint16),
		('combine_len', c_uint16),
		('nbytes', c_uint32),
		('xtype', c_uint32),
		('zero', c_uint32)
               ]


class io_read_t (Structure):
    """
    io_read_t
    Describes the message received for read() requests. 
    The resmgr handler replies with the data read/blocks the client until data is ready or error.
    """
    _fields_ = [('type', c_uint16),
		('combine_len', c_uint16),
		('nbytes', c_uint32),
		('xtype', c_uint32),
		('zero', c_uint32)
               ]

class io_stat_t (Structure):
    """
    io_stat_t
    Describes the input message header used for stat() requests.
    """
    _fields_ = [('type', c_uint16),
		('combine_len', c_uint16),
		('zero', c_uint32)
               ]


class resmgr_context_t (Structure):
    """
    CTP structure.
    Contains the context information for this request.
    This is passed to all io resource manager types. 
    """
    # size verified
    _fields_ = [('rcvid',  c_int),
		('info',   msg_info_t),  #
		('msg',    POINTER (io_read_t)),
		('dpp',    c_void_p),
		('id',     c_int),
		('extra ', c_void_p),
		('msg_max_size', c_uint),
		('status', c_int),
		('offset', c_int),
		('size',   c_int),
		('iov',    iovec) 
		]

class iofunc_attr_t (Structure):
    """
    iofunc_attr structure.
    Defines the "device" attributes. 
    Device specific user variables and data may be appended to this structure. 
    """
    # size verified
    _fields_ = [('mount', c_void_p),
                ('flags', c_uint32),
	        ('lock_tid', c_uint32),
	        ('lock_count', c_int16),
	        ('count', c_int16),
	        ('rcount', c_int16),
	        ('wcount', c_int16),
	        ('rlocks', c_int16),
	        ('wlocks', c_int16),
		('map_list', c_void_p),
		('lock_list', c_void_p),
		('list', c_void_p),
		('list_size', c_int32),
		('nbytes', c_int64),
		('inode', c_int64),
		('uid', c_int),
		('gid', c_int),
		('mtime', c_uint32),
		('atime', c_uint32),
		('ctime', c_uint32),
		('mode', c_uint32),
		('nlinks', c_int32),
		('rdev', c_int32)
		############## Edit user variables after this point
		]

    def sizeof (self):  return sizeof (self)
    def addressof (self):  return addressof (self)

    
    
class iofunc_ocb_t  (Structure):
    """
    OCB structure

    Defines the ocb strucure. It also contains an extra field (Self) that is used by the 
    low level routines. Self is initialised in __init__.  

    An 'Init' class method is provided that is called by the framework when the ocb is initialised.
    The user may use this to to initialise ocb specific data structures. 

    An OCB instance may have additional values addded to instances. 
    """

    # size verified (fixed)
    _fields_ = [('attr', c_void_p),
                ('ioflag', c_int32),
		('offset', c_int64),
		('sflag', c_int16),
		('flags', c_int16),
		('reserved', c_void_p),
		######  Messy but - here we save the ocb instance address
		('Self', c_int32)
		]

    def __init__ (self):
	""" Initialises the OCB. 
	This method is only here to fill in the self referencing that we need later.
	"""
	 
	self.Self= id(self)
	
    def Init (self): 
	""" Potiential user OCB init code. Called when the OCB is created. 
	"""
	pass
    
    def __len__ (self):  return sizeof (self)
    def addressof (self):  return addressof (self)
    
    

class stat_t (Structure):
    """ 
    stat_t
    Definition of the stat_t structure.
    """
    # size verified
    _fields_ = [('st_ino', c_int32),
                ('st_ino_hi',  c_int32),
                ('st_size',  c_int32),
                ('st_size_hi',  c_int32),
		('st_dev',   c_int32),
		('st_rdev',  c_int32),
		('st_uid',   c_int32),
		('st_gid',   c_int32),
		('st_mtime', c_int32),
		('st_atime', c_int32),
		('st_ctime', c_int32),
		('st_mode',  c_int32),
		('st_nlink', c_int32),
		('st_blocksize', c_int32),
		('st_nblocks',   c_int32),
		('st_blksize',   c_int32),
		('st_blocks',   c_int32),
		('st_blocks_hi',    c_int32)
		]

    def __len__ (self):
	return sizeof (self)
    def sizeof (self):  return sizeof (self)
    def addressof (self):  return addressof (self)
		

class resmgr_connect_funcs_t (Structure):
    """
    Resource Manager connect functions.
    """
    _fields_ = [ ('nfuncs', c_uint),
		 ('open',   c_uint32),   # 0x100
		 ('unlink', c_uint32),
		 ('rename', c_uint32),
		 ('mknod', c_uint32),
		 ('readlink', c_uint32),
		 ('link', c_uint32),
		 ('unblock_conn', c_uint32),
		 ('mount', c_uint32)
		 ]
    def __init__ (self):
	self.nfuncs = 8


	
class resmgr_io_funcs_t (Structure):
    '''
    Resource Manager I/O functions.
    '''
    _fields_ = [ ('nfuncs', c_uint),
                 ('read',  c_uint32),    # 0x101
		 ('write', c_uint32),    # 0x102
		 ('close_ocb', c_uint32),   ('stat',  c_uint32),
		 ('notify', c_uint32),      ('devctl', c_uint32), #0x106
		 ('unblock', c_uint32), #0x107
		 ('pathconf', c_uint32),    ('lseek', c_uint32),
		 ('chmod', c_uint32),       ('chown', c_uint32),
		 ('utime', c_uint32),       ('openfd', c_uint32),
		 ('fdinfo', c_uint32),      ('lock', c_uint32),
		 ('space', c_uint32),   #
		 ('shutdown', c_uint32),    ('mmap', c_uint32),
		 ('msg', c_uint32),         ('reserved', c_uint32),
		 ('dup', c_uint32),         ('close_dup', c_uint32),  # 0x116.. io_close
		 ('lock_ocb', c_uint32),    ('unlock_ocb', c_uint32),
		 ('sync', c_uint32),        ('power', c_uint32)
		 ]
		 
    def __init__ (self):
	self.nfuncs = 26
    def addressof (self):  return addressof (self)

	

    
class Resmgr (Message) : #QNX):
    """ 
    Resource manager class.

    This class is able to creates a Resource Manager. 
    It allows the caller to 
    - specify/modify their own attributes structure. 
    - change the ocb, adding variables on the fly. 
    - specify callback methods to be called for message types (e.g. read, write) 
    - manages the blocking waiting for messages. 
    - performs the resmgr_attach
    - Calls threadctl to get privilage
 
    The Callbacks occur in two families - connect and IO. There is usually a need to convert the 
    function parameters to python the defined structures (e.g. Ocb). Convertion methods exist to do this.
    There is no ability for the wrapper library to automatically reply to the caller. All callbacks must
    do their own replying. 
 
    """    
    _RESMGR_NOREPLY = 0x080000000L
    _PULSE_CODE_UNBLOCK = -32
    _PULSE_CODE_DISCONNECT = -33
    _PULSE_CODE_THREADDEATH = -34
    _PULSE_CODE_COIDDEATH = -35
    
    _PULSE_CODE_MINAVAIL  = 0
    _PULSE_CODE_MAXAVAIL = 127

    _io_offset = {'read':   0x1,   'write': 0x2,       'close_ocb': 0x3,
                 'stat':    0x4,   'notify': 0x5,      'devctl': 0x6,
		 'unblock': 0x7,   'pathconf': 0x8,    'lseek': 0x9,
		 'chmod':   0xa,   'chown': 0xb,       'utime': 0xc,
		 'openfd':  0xd,   'fdinfo': 0xe,      'lock': 0xf,
		 'space':   0x10,  'shutdown': 0x11,   'mmap' : 0x12,
		 'msg':     0x13 , 'reserved': 0x14,   'dup': 0x15,
		 'close_dup': 0x16,   # io_close
		 'lock_ocb': 0x17, 'unlock_ocb': 0x18, 'sync': 0x19,
		 'power':   0x1a}

    _connect_offset = {'open': 0x1,     'unlink': 0x2,   'rename': 0x3,
                       'mknod': 0x4,    'readlink': 0x5, 'link': 0x6,
		       'unblock': 0x7,  'mount': 0x8}   

    
    def __init__ (self, Name, Attr=None, Ocb = None, Verbose=0, Flags=0, Chid=-1, RawMode=True):
        """ 
	Resmgr class - __init__ method.
	Creates the necessary library and other library connections.
	Initialises the Attriibutes structure. 
	imports Message  
	Initialises the resmgr. 
	
	@param Name:  The name to be registered (e.g. /dev/gps)
	@param Attr:  An optional/preconfigured Attributes instance. 
	@param Ocb:   The ocb structure. 
	@param Verbose: Sets the verbosity level
	@param Flags: Resmgr_attach flags. See QNX docs.
	@param Chid:  ChannelId.
	"""

	Message.__init__(self)
    
	self._iofunc_stat = self.lib.iofunc_stat
	    
	# use the atribute provided (may be larger) or the default. 
	if Attr == None: Attr = iofunc_attr_t ()
	self.Attr = Attr

	# use the OCB provided or the default.
	if Ocb == None: Ocb = iofunc_ocb_t
	self.Ocb = Ocb
	self.Ocb.offset = 0	

	# import and link C helper functions from resmgrfns
	from resmgrfns import (Init, Run, AddIo, AddConnect, AddPulse)

	self.Init         = Init	# init the resmgr
	self.Run          = Run		# block and handle the messages
	self._AddIo       = AddIo	# add an io function
	self._AddConnect  = AddConnect	# add a connect function
	self.AddPulse	   = AddPulse

	# for use in message passing/replying to the client. 

	self.lib.ThreadCtl (1, 0)	# allow permissions! 
	self.Verbose    = Verbose
	self.DeviceName = Name 
	self.Flags      = Flags	
	self.Chid       = Chid
	self.io_write_t = io_write_t

	# from resmgrfns. Initialise the whole Resmgr. attach etc
	# flags before=1(default) , after=2, dir=0x100

	self.Init (self, self.DeviceName, Attr=self.Attr, Ocb=self.Ocb,
		Verbose=self.Verbose, Flags=self.Flags,
		Chid=self.Chid)

	self.Attr.mtime = self.Attr.ctime = self.Attr.atime = int ( time.time())

	if self.Verbose: print "Resmgr '%s' Initialised." % self.DeviceName 


    def Dump (self, Data, Len = None):
        """ 
	Debug method. Used to dump a memory area in hex, for a specified length.
	@param Data: The data to display
	@param Len: The length of teh display, number of bytes.

        """
        d = cast (pointer(Data), POINTER (c_uint))
        try:
	    _len_ = sizeof(Data) / sizeof (c_uint)
        except:
            _len_ = 8
        if Len:  _len_ = Len
        for i in xrange (_len_):
	    print "%8x " % (d[i]),
	    if (i+1) % 8 == 0: print
        print


    def Report (self, Struct):
        """ 
        Reports the items and values of a passed structure. 
	This is a dumper for ctypes instances. I examines the _fields_ entries and reports their values

	@param Struct: The structure to examine. 
        """
        print "Entries for :", Struct
        for f in Struct._fields_: 
	    temp = getattr (Struct, f[0])
	    try: temp = hex(temp)
	    except: pass
	    print str(f[0]).ljust(20), temp

    def string_at (self, Data, Len):
	"""
	string_at calls the ctypes string_at to display the contents of ctypes data.
	"""
	return string_at (Data, Len)
	
    def AddHandlers (self, **Entries):
	"""  
	Method to add an io or connect function to the tables
	@param Entries: a dictionary of string callback names and their associated callback functions.
	
	Adds the provided callback functions to their correct jump tables.
	Typically this is called : 
	AddHandlers (read=Myread, open=OpenCallback)
 
	"""
	for Entry in Entries:
	    if Entry in self._io_offset:
	        self._AddIo (self._io_offset [Entry], Entries [Entry])
	    elif Entry in self._connect_offset:
	        self._AddConnect (self._connect_offset [Entry], Entries [Entry])
	    else:
	        print "Resmgr.Add - No IO or Connect entry found for %s" % Entry

    def Add (self, **Entries):
        """
	Add an alternate to AddHandlers(). 
	"""
	self.AddHandlers (**Entries)

    def __AddIo (self, **Entries):
	""" 
	Method to add a number of entries in the form 'write=self.MyWrite'
	See AddHandlers.
	"""
	for Entry in Entries:
	    self._AddIo (self._io_offset [Entry], Entries [Entry])

    def __AddConnect (self, **Entries):
	""" 
	Method to add a/many connect function to the connect table. 
	in the form 'open=self.Open'
	See AddHandlers.
	"""
	for Entry in Entries:
	    self._AddConnect (self._connect_offset [Entry], Entries [Entry])

	
    def GetIoData (self, Msg):
	""" 
	Method to create a pointer to the data associated with a message and
	return that data
	@param Msg: Expanded Message_t 
	@return: A ctypes pointer to the data

	""" 
	Data = pointer(cast (pointer (pointer(Msg)[1]), POINTER(c_char)).contents)
	return Data

    def GetConnectData (self, msg, HeaderType=io_open_t):
	"""
	Extract the data from a connect message. Typically io_open_t 
	@param msg: The msg as passed to the connect function. 
	@param HeaderType: Defines the header size. The default is io_open_t. 
	@return: A pointer to the data immediately followign the header
	"""
	Msg = cast (msg, POINTER(HeaderType))
	Data = cast (Msg, POINTER(c_char))
	_size = sizeof (HeaderType) -4
	if HeaderType == io_open_t: Data = Data [_size: _size+Msg.contents.path_len]
	return Data 


    # decorator
    #def IoParamsX (fn):
	#def _fix (self, ctp, msg, Ocb):
	#    (Ctp, Msg) = self.CvtIoParams (ctp, msg) 
	#    fn (self, Ctp, Msg, Ocb)
	#    return self._RESMGR_NOREPLY
#	return _fix
    
    def CvtIoParams (self, ctp, msg, HeaderType=io_write_t): #, ocb):  
	"""
	Converts and extracts the ctp and message data from the addresses that were passed to an IO callback
	The ocb is correctly passed and doesnt need conversion.  
	@param ctp: The context pointer
	@param Msg: The message pointer
	@param HeaderType: The type of the header. (default io_write_t)  
	@return: a tuple with the Ctp and Message data in python 

	""" 
	Ctp = cast (ctp, POINTER(resmgr_context_t)).contents
	if msg != 0:
	    Msg = cast (msg, POINTER(HeaderType)).contents
	else:
	    Msg = None

	return (Ctp, Msg)

    def CvtConnectParams (self, ctp, msg, HeaderType=io_open_t):  
	""" 
	Converts and extracts the ctp and message data from the addresses that were passed to a connect callback
	The ocb is correctly passed and doesnt need conversion.  
	Extract the C addressed structures and convert them to ctype structs.
	@param ctp: The context pointer
	@param msg: The message pointer
	@param HeaderType: The type of the header. (default io_open_t)  
	@return: a tuple with the Ctp and Message data in python 
	"""
	Ctp = cast (ctp, POINTER(resmgr_context_t)).contents
	Msg = cast (msg, POINTER(HeaderType)).contents

	return (Ctp, Msg)


# decorator
#def IoParamsY (fn):
#    def _fix (self, ctp, msg, Ocb):
#        (Ctp, Msg) = Resmgr.CvtIoParams (ctp, msg) 
#        fn (self, Ctp, Msg, Ocb)
#        return Resmgr._RESMGR_NOREPLY
#    return _fix
    
def CvtAddr2Object (Addr, Object):
    return cast (Addr, POINTER(Object)).contents 

def Cvt2Pulse (pulse_p):
	return cast (pulse_p, POINTER(pulse_t)).contents

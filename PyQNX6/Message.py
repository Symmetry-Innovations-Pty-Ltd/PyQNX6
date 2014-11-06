#!/usr/local/bin/python
#import pdb
'''
Symmetry Innovations Pty Lyd
QNX Target Project.


'''
import sys, os, time, cPickle

from ctypes import *

from PyQNX6 import (QNX, name_attach_t, msg_info_t, 
			pulse_t, sigevent,
			)  

__version__ = '0.1'
__author__='Andy Rhind (Symmetry Innovations)'

#####################################
class Connect (QNX):
    """
    Connect class. Holds the Connect/Channel related functions.
    Ones used to create/destroy messaging connections also name functions.
    - ChannelCreate, 
    - ChannelDestroy
    - ConnectAttach, 
    - ConnectDetach
    - name_attach
    - name_detach
    - name_open, 
    - name_close
    
    This class contains both 'server' and 'client' methods.
    This class will maintain one Server link and/or one Client link,
    create another instance for more links. 

    """
    chid = None
    coid = None
    dpp  = None

    __naresult = name_attach_t()  # create the attach structure
    
    def __init__ (self):
	"""
	Intialise the Connect class. 
	Uses the QNX class to provide libc connectivity.
	Defines the ctypes functions. 
	"""
	if QNX.lib == None:
	    QNX.__init__(self)    # init libc

	self.chid = None
	self.coid = None
	self.dpp = None

	# channel related methods
	self._ChannelCreate = self.lib.ChannelCreate
	self._ChannelCreate.argtypes = [c_int]
	self._ChannelDestroy = self.lib.ChannelDestroy
	self._ChannelDestroy.argtypes = [c_int]

	# connect related methods
	self._ConnectAttach = self.lib.ConnectAttach
	self._ConnectAttach.argtypes= [c_int, c_int, c_int, 
	                               c_int, c_int]
	self._ConnectDetach = self.lib.ConnectDetach
	
	# name related methods
	self._name_attach = self.lib.name_attach
	self._name_attach.argtypes = [c_int, c_char_p, c_int]
	self._name_detach = self.lib.name_detach
	self._name_detach.argtypes = [c_void_p, c_int]
	self._name_open = self.lib.name_open
	self._name_open.argtypes = [c_char_p, c_int]
	

    _NTO_CHF_FIXED_PRIORITY  = 1 
    _NTO_CHF_UNBLOCK         = 2
    _NTO_CHF_THREAD_DEATH    = 4
    _NTO_CHF_DISCONNECT      = 8
    _NTO_CHF_SENDER_LEN      = 0x20
    _NTO_CHF_COID_DISCONNECT = 0x40
    _NTO_CHF_REPLY_LEN	     = 0x80

    def ChannelCreate (self, Flags=0):
	"""
	ChannelCreate (Server)
	@param Flags: set to zero (default)
	@return The channel id or None if error	
	
	"""
	__Result = self._ChannelCreate ( c_int( int(Flags)))
	if __Result != -1: self.chid = __Result
	else: self.chid = None

	return self.chid
    
    def ChannelDestroy (self):
	"""
	ChannelDestroy (Server)
	(if one exists) 
	@return The result of the ChannelDestroy call. See QNX docs. 
	"""
	__Result = None
	if self.chid != None: 
	    __Result = self._ChannelDestroy ( c_int (self.chid))
	self.chid = None
	return __Result
   
    def ChannelOk (self):
	return not (self.chid == None or self.chid == -1)
	 
    def ConnectionOk (self):
	return not (self.coid == None or self.coid == -1)
	 
    def ConnectAttach (self, Nd=0, Pid=0, Chid=None,
                              Index=0x40000000, # nto_side_channel
                              Flags=0):
	"""
	ConnectAttach (Client)
	Attach to the Channel defined. 
	@param Nd: Node descriptor
	@param Pid: Process Id
	@param Chid: Channel Id
	@param Index: set to the side_channel 
	@param Flags: 0 
	@return Connection Id. 
	@raise Error if there is no channel to attach to. 

	"""
	if Chid == None: Chid = self.chid

	if Chid == None or Chid == -1: raise "No coid to receive from."
	self.coid = self._ConnectAttach (Nd, Pid, Chid, Index, Flags)

	return self.coid
    
    def ConnectDetach (self):
	"""
	ConnectDetach (Client) Detach from the connection.
	(if one exists)
	"""
	__Result        = None
	if self.coid != None:
	    __Result = self._ConnectDetach (self.coid)
	self.coid = None
	return __Result
    
    def CreateAndAttach (self):
	"""
	CreateAndAttach. Creates a Channel then Connects to it. 
	This is a useful method when using timers and interrupts.

	"""
	self.ChannelCreate ()
	self.ConnectAttach ()
	return self
    
    #
    # name management functions.
    #
    def name_attach (self, Name, Global= False):
	"""
	name_attach: (Server)
	Attached the provided name to this process. 
	Forms a Name/Channel that clients are able to Connect to.    
	
	@param Name: the name that will be registered. 
	@param Global: True if the name is to be registered Globally, else locally.

        @return the channel id, or None if error
	The chid and dpp are set in the instance.
 
        See - QNX.WaitForName
	"""
	__Flag = 0
	if Global: __Flag = 2  # NAME_FLAG_ATTACH_GLOBAL
	self._name_attach.restype = c_void_p  # cant use - name_attach_t
	
	self.__naresult = self._name_attach (c_int(0),
			 c_char_p (Name),
			 c_int(__Flag))

	if self.__naresult == None:
	    self.chid = self.dpp = None
	    #print "name_attach: couldnt attach", self.__naresult
	    return None

	self.__naresult = cast (self.__naresult, POINTER (name_attach_t)).contents
	
	self.chid = self.__naresult.chid
	self.dpp  = self.__naresult.dpp
	return self.chid


    def name_detach (self):
	"""
	name_detach: (Server) Detached the name. 
	"""
	if self.__naresult != None: 
	    __Result = self._name_detach (byref(self.__naresult), c_int(0))
	    self.chid = self.dpp = self.__naresult = None
	    return __Result

	return None

    
    def name_open (self, Name, Global= False):
	"""
	name_open: (Client) Opens & connects to an existing name. 
	@param Name: the name that will be connected to. 
	@param Global: True if the name is registered Globally, else locally.

        @return the connection id, or None if error
	"""
	__Flag = 0
	if Global:  
	    __Flag = 2
	
	self.coid = self._name_open (c_char_p (Name), c_int(__Flag))
	
	if self.coid == -1: 
	    self.coid = None
	return self.coid
    
    def name_close (self):
	"""
	name_close: (Client) 
	Closes the Connection.
	"""
	if self.coid != None:
	    __Result = self.lib.name_close (self.coid)
	    self.coid = None
	    return  __Result

	return None
   


##########################################################

class Message (Connect):
    """ 
    Class provides support for Send, Receive and Reply Functions.
    - MsgSend
    - MsgReceive
    - MsgReply
    - MsgInfo
    - MsgError

    """
    rcvid = None
    info  = msg_info_t()
    
    def __init__ (self, Name = None, Attach = True, Global = False, RawMode = True):
	"""
	Instansiate the Message class.
	Set globals to default values. 
	Creates connections to the libc C functions.
	
	@param Name: if provided, attach or open this name.
	@param Attach: Attach or Open the Name.
	@param Global: the Name is Global or Local. Default (Local)
        @param RawMode: when sending & receiving use Rawdata, the default data is raw rather than pickled. 
  
        The defaults are :
        Attach True - will try to attach else
            will try to 'open'.
        Global (name) False, 
        Raw mode.  
	"""
	Connect.__init__ (self)
	self.rcvid = None
	self._Buffer = None
	self._BufferLen = 0
	self.RawMode    = RawMode
	self.RxData     = None

	self._MsgSend         = self.lib.MsgSend
	self._MsgReceive      = self.lib.MsgReceive
	self._MsgReply        = self.lib.MsgReply
	self._MsgRead         = self.lib.MsgRead
	self._MsgError        = self.lib.MsgError
	self._MsgInfo         = self.lib.MsgInfo
	self._MsgSendPulse    = self.lib.MsgSendPulse
	self._MsgDeliverEvent = self.lib.MsgDeliverEvent

	if Name:
	    if Attach :     # attach to a this name
		self.name_attach (Name, Global)
	    else:
		self.name_open (Name, Global)

	
    def MsgInfo (self, Rcvid=None):
	"""
	MsgInfo(), wrapper.
	@return the MsgInfo structure, by calling MsgInfo
	"""
	if Rcvid == None:  Rcvid = self.rcvid

	Result = self._MsgInfo (c_int (Rcvid), byref (self.info))
	return self.info
   
 
    def MsgSend (self, TxData, RxLen=1024, RawMode = None):
	"""
	MsgSend() wrapper.
	@param TxData: Data to be transmitted to the connection Id. 
	@param RxLen: the default rx buffer length
	@param RawMode: This send and reply data will be raw of pickled. The instance setting is not changd. 
	@return A tuple containg (The result from the MsgSend and the reply length), or (-1, 0) if error. 

	Replied data is held in RxData. 

	Sends TxData to the Connection defined by coid.
	If Raw then the TxData is sent as is else the data is pickled. 
        A buffer is allocated if more size is required. 
	If specified then replied data is un-cPickle'd. 
	
	"""
	if self.coid == None: return (-1, 0)

	TempRaw = self.RawMode
	if RawMode != None: TempRaw = RawMode
	
	if not TempRaw:		# pickle this
	    TxData = cPickle.dumps (TxData)
	elif type (TxData) != str :
	    TxData = repr (TxData)

	_Len     = len (TxData)
	if RxLen > self._BufferLen:
	    self._AllocRxBuffer (RxLen)

	if TempRaw:	# clear the reply buffer if raw reply. 
	    self._Buffer = (c_char *RxLen) () 
        Result = self._MsgSend (self.coid, 
	           c_char_p (TxData), _Len,
		   self._Buffer, 
		   self._BufferLen)
	
	self.RxData = None
	if (Result != -1):
	    if TempRaw == False:
		self.RxData = cPickle.loads (self._Buffer.value)
		return (Result, 1) # is always 1

	    if type (self._Buffer.value) != str :		
		self.RxData = repr (self._Buffer.value)
	    else:
		self.RxData = self._Buffer [:self._BufferLen] #.value
	    return (Result, len (self.RxData))
	else:
	    return (Result, 0)


    def MsgSendPulse (self, Coid=None, Priority=10, Code=0, Value=0):
	"""
	MsgSendPulse() wrapper.
	Creates and sends a pulse to the Coid.
	@param Coid: The connectionId to send the pulse to
	@param Priotity: The proirity of the pulse
	@param Code: The code associated with the pulse. 
	@param Valus: The value associated with the pulse

	@return The result of the call to MsgSendPulse.
	"""
	if Coid == None: Coid = self.coid
	return self._MsgSendPulse (Coid, Priority, Code, Value)


    def MsgRead (self, Rcvid, Buffer, Bytes, Offset = 0):
	"""
	MsgRead() wrapper. Performs a MsgRead using the passed Rcvid.
	(Work to be done, testing ) 
	"""
	return self._MsgRead (Rcvid, Buffer, Bytes, Offset)


    def MsgDeliverEvent (self, Sigevent, Rcvid=None):
	"""
	MsgDeliverEvent() wrapper. Delivers the Sigevent to rcvid using MsgDeliverEvent 
	@param Sigevent: The event to be delivered
	@param Rcvid: The event destination.
	@return The result of the MsgDeliverEvent call. 	

	"""
	if Rcvid == None: Rcvid = self.rcvid
	return self._MsgDeliverEvent (Rcvid, pointer(Sigevent))


    def MsgReceive (self, RxLen= 1024, RawMode = None):
	"""
	MsgReceive () wrapper. Perfoms a MsgReceive using the channelid. 

	@param RxLen: The default Rx buffer length.
	@param RawMode: The received data is raw or pickled and converted as necessary. 
	@return A tuple with the (rcvid and the length of the received data)
 
	A persistant receive buffer is allocated. If the receive buffer size is exceeded
	then a new buffer is allocated and a MsgRead performed.
	If a pulse   is received: a tuple with rcvid and the pulse is returned.
	If a message is received: a tuple with rcvid and the un-cPickle'd data LENGTH is returned
	Use self.RxData to process the received data.

	@raise If There is no chid
	"""

	if self.chid == None: raise "No chid to receive from."
	if RxLen > self._BufferLen: self._AllocRxBuffer (RxLen)
	
	self.rcvid = self._MsgReceive (self.chid, self._Buffer,
	                      int (self._BufferLen), byref (self.info))

	if self.rcvid == 0:
	    # We have a pulse. Cast it then return. 
	    # NB we must add code that will cleanup after a system pulse. 
	    self.pulse = cast (self._Buffer, POINTER (pulse_t)).contents
	    self.RxData = self.pulse
	    return (self.rcvid, self.pulse)

	if self._BufferLen < self.info.srcmsglen:
	    self._AllocRxBuffer (self.info.srcmsglen)
	    self.MsgRead (self.rcvid, self._Buffer, int (self.info.srcmsglen), 0)

	if (self.rcvid >= 0): # and (self._BufferLen > 0):
	    TempRaw = self.RawMode
	    if RawMode != None: TempRaw = RawMode

	    if not TempRaw:
		self.RxData = cPickle.loads (self._Buffer.value [:self.info.srcmsglen])
		return (self.rcvid, 1)

	    TempData = self._Buffer.value [:self.info.srcmsglen]
	    if type (TempData) != str: 
		self.RxData = repr (TempData)
	    else:
		self.RxData = TempData
	    return (self.rcvid, len(self.RxData))

	return (self.rcvid , None)


    def _AllocRxBuffer (self, Len):
	"""
	Internal function : Allocates/Reallocates a buffer for message handling
	"""
	if self._Buffer: del (self._Buffer)
	self._Buffer = create_string_buffer (Len) # andy (c_char *Len) ()
	self._BufferLen = Len
	

    #def GetRxData (self):
	"""
	Helper function. Used after a MsgSend call, this will return the 
	replied data and its length as a tuple. 
	"""
	#if self._BufferLen >= 0:
	#    return (self._Buffer.value, self._BufferLen)
	#else:
	#    return (None, 0)


    def MsgReply (self, Status, Data=None, Rcvid = None, RawMode = None, Len=None):
	"""
	MsgReply() wrapper. Performs a MsgReply. cPickles the data and replies with the status and data.
	@param Status: The statis integer value to return to the caller. 
	@param Data: The data to reply with
	@param Rcvid: The receiveId to reply to. (optional) 
	@param RawMode: Reply with the data or pickle it then reply.
	@param Len: Reply with only len bytes. 

	@return the result of the MsgReply call. See QNX docs. 
	"""
	def _GetLen (PassedLen, DataLen):
	    if PassedLen == None:
		return DataLen
	    else: 
		return PassedLen

	if Data == None: Data = ""
	
	TempRaw = self.RawMode
	if RawMode != None: TempRaw = RawMode
	
	if not TempRaw:
	    Data = cPickle.dumps (Data)
	    _Len = len (Data)
	else:
	    if hasattr (Data, "_fields_"):
		_Len = _GetLen(Len, len(Data))
	        Data = byref (Data)
	    else:
	     	if type (Data) != str:
		    Data = repr (Data)
		    _Len = _GetLen (Len, len (Data)) 
		    print "replyStr: len=", _Len
		else:
		    _Len = _GetLen (Len, len (Data))	
	    #if Len != None:  _Len = len

	if Rcvid == None:  Rcvid = self.rcvid
	#print "msgreplying- %d %d len=%d \'%s\'" % (Rcvid, Status, _Len, repr (Data)) 
	_Result    = self._MsgReply (int (Rcvid),
	                       int (Status),
			       cast (Data, POINTER (c_char)),
			       int (_Len) )

	return _Result


    def MsgError (self, Error, Rcvid = None):
	"""
	MsgError() wrapper. Returns a MsgError to the rcvid.
	@param Error: The error number to reply with.
	@param Rcvid: The rcvid to reply to. 

	@return The result of the MsgError call. See QNX docs. 

	"""
	if Rcvid == None:  Rcvid = self.rcvid
	Result    = self._MsgError (int(Rcvid), int (Error))
			    
	return Result



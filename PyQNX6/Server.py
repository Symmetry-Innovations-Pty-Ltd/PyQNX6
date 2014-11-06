#!/usr/local/bin/python
#import pdb
'''
Symmetry Innovations Pty Lyd
QNX Target Project.


'''
import sys, os

from PyQNX6.Message  import Message  as Message

__version__ = '0.1'
__author__='Andy Rhind (Symmetry Innovations)'

#####################################

import threading


class QNXServer  (Message):

    def __init__ (self, Name, Function, Global=False, RawMode=False):
        Message.__init__ (self, Name, Attach=True, Global=Global, \
			RawMode=RawMode)
	self.Name = Name
	self.Global = Global
	self.RawMode = RawMode
	self.Function = Function
	#self.s = Message (self.Name, Attach=True, Global=self.Global, \
	#		RawMode=self.RawMode)
    
    def Run (self):
	Done = False
 	while (not Done):
            (Rcvid, Data) 		= self.MsgReceive ()
	    try: ReturnStatus, Data	= self.Function (self, Rcvid, self.RxData)
	    except (StopIteration, KeyboardInterrupt, EOFError): 
		Done = True
		ReturnStatus, Data = -1, None
		print  "DONE. Server exiting."
	    if Rcvid:
	        Result = self.MsgReply (ReturnStatus, Data)
       


class QNXServerThreaded  (Message):

    def __init__ (self, Name, Function, Global=False, RawMode=False, Start=False):
        Message.__init__ (self)
	self.Name = Name
	self.Global = Global
	self.RawMode = RawMode
	self.Function = Function
	self.s = Message (self.Name, Attach=True, Global=self.Global, \
			RawMode=self.RawMode)
	if Start: self.Start()
    
    class _Server (threading.Thread):
        def __init__ (self, Server, Function):
           threading.Thread.__init__ (self)
	   self.Server = Server
	   self.Function = Function

        def run (self):
	    #print "QNXServer class thread- started"
	    Done = False
 	    while (not Done):
	        (Rcvid, Data) 		= self.Server.MsgReceive ()
	        try: ReturnStatus, Data	= self.Function (self, Rcvid, self.Server.RxData)
		except (StopIteration, KeyboardInterrupt, EOFError): 
			Done = True
			ReturnStatus, Data = -1, None
			print  "DONE. server exiting."
		if Rcvid:
		    Result = self.Server.MsgReply (ReturnStatus, Data)
       
    def Start (self):
        ThisServer = self._Server (self.s, self.Function)
        ThisServer.start ()
	return ThisServer




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

from PyQNX6.core import WaitforAttach

class QNXClient (Message):

    def __init__ (self, Name, Global=False, RawMode=False, WaitFor=True):
	Message.__init__ (self)
	self.RawMode = RawMode
	self.Global  = Global

	if WaitFor:
	    WaitforAttach (Name, Global)

        self.coid = self.name_open (Name, Global)
	self.Name = Name


   	   



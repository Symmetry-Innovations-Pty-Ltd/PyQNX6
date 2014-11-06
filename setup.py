
'''
Symmetry Innovations Pty Ltd

pyqnx6@symmetry.com.au

'''
from distutils.core  import setup, Extension

from distutils.command.install import INSTALL_SCHEMES

for scheme in INSTALL_SCHEMES.values():
	scheme ['data'] = scheme ['platlib']


setup (name ='PyQNX6', 
	author ='Andy Rhind, Symmetry Innovations Pty Ltd',
	author_email = 'pyqnx6@symmetry.com.au',
	description = 'QNX/Python package',
	license = 'MIT',
	keywords = ['QNX, Message Passing',],
	url = 'http://symmetry.com.au/PyQNX6',
	version='0.1.0',
	platforms = ['QNX6'],
	package_dir={'PyQNX6': 'PyQNX6'},
	packages=['PyQNX6' ] ,   #, 'PyQNX6/tests'],
	data_files = [ 'PyQNX6/resmgrfns.so', 'PyQNX6/Portio.so'], 
	)



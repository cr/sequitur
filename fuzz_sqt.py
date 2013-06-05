#!/usr/bin/env python

from sqt import *
import sys
import random
import unittest
import logging as log
log.basicConfig( level=log.WARNING )
from IPython import embed

#########################################################################################
class Test_Fuzzing_Sequitur( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.ERROR )
		log.info( " ##### BEGIN %s ##############################################" % cls )

	@classmethod
	def tearDownClass( cls ):
		log.info( " ##### END %s ##############" % cls )

	def setUp( self ):
		self.s = Sequitur()

	def test_sequitur_fuzz( self ):
		def rndstring():
			s = ""
			for b in xrange( 0, 16 ):
				char = chr( random.randint( 0, 3 ) + ord( 'a' ) )
				rep = random.randint( 1, 5 )
				s += char*rep
			return s
		for x in xrange( 8000 ):
			s = Sequitur()
			rnd = list( rndstring() )
			try:
				for c in rnd:
					s.append( c )
					#print_state( s.index )
				sys.stderr.write( '.' )
			except:
				log.error( "crash with %s" % ''.join(rnd) )
				raise
			#self.assertEqual( [x for x in s.walk()], rnd )


#########################################################################################
if __name__ == '__main__':
    unittest.main()


#!/usr/bin/env python

from sqt import *
import unittest
import logging as log
log.basicConfig( level=log.ERROR )
from IPython import embed

#########################################################################################
class Test_AA_Symbol( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.ERROR )
		log.info( " ##### BEGIN %s ##############################################" % cls )
		# temporarily disable makeunique to prevent failure on low-level linkage
		cls.tmpmakeunique = Rule.makeunique
		Rule.makeunique = Rule.makeunique_disabled

	@classmethod
	def tearDownClass( cls ):
		Rule.makeunique = cls.tmpmakeunique
		log.info( " ##### END %s ##############" % cls )

	def setUp( self ):
		index.reset()
		Rule.reset()

	def test_symbol_instance( self ):
		r = Rule()
		g = Symbol( r, guard=True)
		a = Symbol( 1 )
		self.assertTrue( isinstance( g, Symbol ) )
		self.assertTrue( isinstance( g.ref, Symbol ) )
		self.assertIs( g.ref.ref, r )
		self.assertTrue( isinstance( a, Symbol ) )

	def test_symbol_values( self ):
		a = Symbol( 1 )
		self.assertEqual( a.ref, 1 )
		a.ref = 2
		self.assertEqual( a.ref, 2 )

	def test_symbol_is_guard( self ):
		r = Rule()
		g = Symbol( r, guard=True )
		a = Symbol( 1 )
		self.assertTrue( g.is_guard() )
		self.assertTrue( r.guard.is_guard() )
		self.assertFalse( a.is_guard() )

	def test_symbol_linkage( self ):
		a = Symbol( 1 )
		b = Symbol( 2 )
		self.assertEqual( a.next, None )
		self.assertEqual( a.prev, None )
		self.assertEqual( b.next, None )
		self.assertEqual( b.prev, None )
		b.prevconnect( a )
		self.assertEqual( a.prev, None )
		self.assertEqual( b.next, None )
		self.assertIs( a.next, b )
		self.assertIs( b.prev, a )
		b.prevdisconnect()
		self.assertEqual( a.next, None )
		self.assertEqual( a.prev, None )
		self.assertEqual( b.next, None )
		self.assertEqual( b.prev, None )
		a.nextconnect( b )
		self.assertEqual( a.prev, None )
		self.assertEqual( b.next, None )
		self.assertIs( a.next, b )
		self.assertIs( b.prev, a )
		a.nextdisconnect()
		self.assertEqual( a.next, None )
		self.assertEqual( a.prev, None )
		self.assertEqual( b.next, None )
		self.assertEqual( b.prev, None )

	def test_symbol_floating_exception( self ):
		a = Symbol( 1 )
		with self.assertRaises( AttributeError ): a.next.next
		with self.assertRaises( AttributeError ): a.prev.prev

	def test_symbol_digrams( self ):
		g = Symbol( Rule(), guard=True )
		a = Symbol( 1 )
		b = Symbol( 2 )
		g.nextconnect( a )
		a.nextconnect( b )
		b.nextconnect( g )
		self.assertEqual( g.digram(), (None,a) )
		self.assertEqual( a.digram(), (a,b) )
		self.assertEqual( b.digram(), (b,None) )
		self.assertEqual( g.refdigram(), (None,1) )
		self.assertEqual( a.refdigram(), (1,2) )

	def test_symbol_replace_digram( self ):
		a = Symbol( 1 )
		b = Symbol( 2 )
		c = Symbol( 3 )
		d = Symbol( 4 )
		e = Symbol( 5 )
		a.nextconnect( b )
		b.nextconnect( c )
		c.nextconnect( d )
		ret = b.replace_digram( e )			
		self.assertIs( a.next, e )
		self.assertIs( e.next, d )
		self.assertIs( d.prev, e )
		self.assertIs( e.prev, a )
		self.assertEqual( b.prev, None )
		self.assertEqual( b.next, None )
		self.assertEqual( c.prev, None )
		self.assertEqual( c.next, None )
		self.assertIs( ret, e )

	def test_symbol_replace_symbol( self ):
		a = Symbol( 1 )
		b = Symbol( 2 )
		c = Symbol( 3 )
		d = Symbol( 4 )
		e = Symbol( 5 )
		f = Symbol( 6 )
		a.nextconnect( b )
		b.nextconnect( c )
		d.nextconnect( e )
		e.nextconnect( f )
		b.replace_symbol( d, e )			
		self.assertIs( a.next, d )
		self.assertIs( d.next, e )
		self.assertIs( e.next, c )
		self.assertIs( c.prev, e )
		self.assertIs( e.prev, d )
		self.assertIs( d.prev, a )
		self.assertEqual( a.prev, None )
		self.assertEqual( b.prev, None )
		self.assertEqual( b.next, None )
		self.assertEqual( c.next, None )
		self.assertEqual( f.prev, None )
		self.assertEqual( f.next, None )

#########################################################################################
class Test_BA_Rule( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.ERROR )
		log.info( " ##### BEGIN %s ##############################################" % cls )
		# temporarily disable makeunique to prevent failure on low-level linkage
		cls.tmpmakeunique = Rule.makeunique
		Rule.makeunique = Rule.makeunique_disabled

	@classmethod
	def tearDownClass( cls ):
		Rule.makeunique = cls.tmpmakeunique
		Rule.reset()
		log.info( " ##### END %s ##############" % cls )

	def setUp( self ):
		index.reset()
		Rule.reset()

	def test_rule_instance( self ):
		r = Rule()
		self.assertTrue( isinstance( r, Rule ) )
		self.assertTrue( r.guard.is_guard() )
		self.assertIs( r.guard.ref.ref, r )
		self.assertIs( r.guard.next, r.guard )
		self.assertIs( r.guard.prev, r.guard )
		self.assertEqual( r.refcount(), 0 )

	def test_rule_append( self ):
		r = Rule()
		a = r.append( 1 )
		self.assertTrue( r.guard.is_guard() )
		self.assertTrue( isinstance( a, Symbol ) )
		self.assertIs( r.guard.next, a )
		self.assertIs( r.guard.next.next, r.guard )
		self.assertIs( r.guard.prev, a )
		self.assertIs( r.guard.prev.prev, r.guard )
		b = r.append( 2 )
		self.assertIs( r.guard.next, a )
		self.assertIs( r.guard.next.next, b )
		self.assertIs( r.guard.next.next.next, r.guard )
		self.assertIs( r.guard.prev, b )
		self.assertIs( r.guard.prev.prev, a )
		self.assertIs( r.guard.prev.prev.prev, r.guard )

	def test_rule_each( self ):
		r = Rule()
		a = r.append( 1 )
		b = r.append( 2 )
		self.assertEqual( [ref for ref in r.each()], [1,2] )
		self.assertEqual( [ref for ref in r.eachsym()], [a,b] )

	def test_rule_walkdump( self ):
		r = Rule()
		r.append( 1 )
		r.append( 2 )
		s = Rule()
		s.append( 3 )
		s.append( r )
		s.append( 4 )
		#print_state()
		self.assertEqual( r.dump(), [1, 2] )
		self.assertEqual( r.walk(), [1, 2] )
		self.assertEqual( s.dump(), [3, r, 4] )
		self.assertEqual( s.walk(), [3, 1, 2, 4] )

	def test_rule_replace_digram( self ):
		r = Rule()
		r.append( 1 )
		r.append( 2 )
		s = Rule()
		a = s.append( 3 )
		b = s.append( 4 )
		c = s.append( 5 )
		d = s.append( 6 )
		ret = r.replace_digram( b )
		self.assertEqual( r.walk(), [1, 2] )
		self.assertEqual( s.dump(), [3, r, 6] )
		self.assertEqual( s.walk(), [3, 1, 2, 6] )
		self.assertIs( s.guard.prev, d )
		self.assertIs( s.guard.prev.prev.ref, r )
		self.assertIs( s.guard.prev.prev.prev, a )
		self.assertIs( s.guard.prev.prev.prev.prev, s.guard )
		self.assertEqual( r.refcount(), 1 )
		self.assertIs( ret, a.next )
		self.assertTrue( ret in r.refs )

	def test_rule_delete( self ):
		r = Rule()
		r.append( 1 )
		r.append( 2 )
		s = Rule()
		a = s.append( 3 )
		b = s.append( 1 )
		c = s.append( 2 )
		ret = r.replace_digram( b )
		self.assertEqual( r.refcount(), 1 )
		self.assertTrue( ret in r.refs )
		r.delete()
		self.assertEqual( r.refcount(), 0 )
		self.assertEqual( s.dump(), [3,1,2] )

#########################################################################################
class Test_CA_Index( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.DEBUG )
		log.info( " ##### BEGIN %s ##############################################" % cls )

	@classmethod
	def tearDownClass( cls ):
		index.reset()
		Rule.reset()
		log.info( " ##### END %s ##############" % cls )

	def setUp( self ):
		index.reset()
		Rule.reset()

	def test_index_instance( self ):
		self.assertTrue( isinstance( index, Index ) )

	def test_index_keys( self ):
		# TODO: test with more datatypes
		# TODO: test with rule references
		index.reset()
		r = Rule()
		a = r.append( 1 )
		b = r.append( 2 )
		self.assertEqual( index.key( a ), "1"+index.keyseparator+"2" )
		index.reset( keyseparator="foo" )
		self.assertEqual( index.key( a ), "1foo2" )
		self.assertEqual( index.key( a ), "1"+index.keyseparator+"2" )
		index.reset()
		self.assertEqual( index.key( a ), "1"+index.keyseparator+"2" )
		self.assertEqual( index.key( b ), "2"+index.keyseparator+"None" )
		self.assertEqual( index.key( r.guard ), "None"+index.keyseparator+"1" )

	def test_index_learning( self ):
		# temporarily disable makeunique to prevent failure on low-level linkage
		tmpmakeunique = Rule.makeunique
		Rule.makeunique = Rule.makeunique_disabled
		# calls to learn() and forget() are implicit through symbol linkage/unlinkage
		unlearned = Symbol( 1 )
		unlearnedb = Symbol( 2 )
		unlearned.next = unlearnedb
		unlearned.prev = unlearned
		self.assertFalse( index.seen( unlearned ) )
		a = Symbol( 1 )
		self.assertFalse( index.seen( unlearned ) )
		b = Symbol( 2 )
		self.assertFalse( index.seen( unlearned ) )
		a.nextconnect( b )
		self.assertTrue( index.seen( unlearned ) )
		self.assertIs( index.seen( unlearned ), a )
		self.assertTrue( index.seen( a ) )
		with self.assertRaises( AttributeError ): Symbol.index.seen( b ) # b.next==None
		a.nextdisconnect()
		self.assertFalse( index.seen( unlearned ) )

		r = Rule()
		c = r.append( 1 )
		self.assertFalse( index.seen( c ) )
		self.assertFalse( index.seen( c.prev ) ) # c.prev is guard
		d = r.append( 1 )
		self.assertFalse( index.seen( d ) )
		self.assertFalse( index.seen( unlearned ) )
		e = r.append( 2 )
		self.assertTrue( index.seen( unlearned ) )

		Rule.makeunique = tmpmakeunique

	def test_index_makeunique( self ):
		r = Rule()
		a = r.append( 1 )
		b = r.append( 2 )
		s = Rule()
		c = s.append( 3 )
		d = s.append( 1 )
		e = s.append( 2 )
		f = s.append( 4 )
		self.assertEqual( s.dump(), [3,r,4] )
		self.assertEqual( s.walk(), [3,1,2,4] )

	def test_index_killref( self ):
		r = Rule()
		r.append( 1 )
		r.append( 2 )
		r.append( 3 )
		r.append( 4 )
		r.append( 2 )
		#print_state()
		self.assertEqual( len(Rule.rules), 1 )
		self.assertIs( Rule.rules[0], r )
		self.assertEqual( r.walk(), [1,2,3,4,2] )
		#print "1#######################"
		#print_state()
		r.append( 3 )
		self.assertEqual( len(Rule.rules), 2 )
		s = Rule.rules[1]
		self.assertEqual( r.dump(), [1,s,4,s] )
		self.assertEqual( s.dump(), [2,3] )
		self.assertEqual( r.walk(), [1,2,3,4,2,3] )
		self.assertEqual( len(s.refs), 3 )
		self.assertTrue( r.guard.next.next in s.refs )
		self.assertTrue( r.guard.next.next.next.next in s.refs )
		#print "2#######################"
		#print_state()
		r.append( 1 )
		self.assertEqual( r.dump(), [1,s,4,s,1] )
		self.assertEqual( s.dump(), [2,3] )
		self.assertEqual( r.walk(), [1,2,3,4,2,3,1] )
		self.assertEqual( len(s.refs), 3 )
		self.assertTrue( r.guard.next.next in s.refs )
		self.assertTrue( r.guard.next.next.next.next in s.refs )
		#print "3#######################"
		#print_state()
		r.append( 2 )
		self.assertEqual( r.dump(), [1,s,4,s,1,2] )
		self.assertEqual( s.dump(), [2,3] )
		self.assertEqual( r.walk(), [1,2,3,4,2,3,1,2] )
		self.assertEqual( len(s.refs), 3 )
		self.assertTrue( r.guard.next.next in s.refs )
		#elf.assertTrue( r.guard.next.next.next.next in s.refs )
		#print "4#######################"
		#print_state()
		r.append( 3 )
		#print_state()
		#self.assertEqual( len(Rule.rules), 3 )
		#self.assertFalse( 1 in Rule.rules )
		#t = Rule.rules[2]
		#self.assertEqual( r.dump(), [t,4,2,3,t] )
		#self.assertEqual( t.dump(), [1,2,3] )
		#self.assertTrue( r.guard.next in t.refs )
		#self.assertTrue( r.guard.next.next.next.next.next in t.refs )
		#print "5#######################"
		#print_state()
		r.append( 4 )
		#print_state()
		self.assertEqual( r.walk(), [1, 2, 3, 4, 2, 3, 1, 2, 3, 4] )

#########################################################################################
class Test_DA_Sequitur( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.ERROR )
		log.info( " ##### BEGIN %s ##############################################" % cls )

	@classmethod
	def tearDownClass( cls ):
		log.info( " ##### END %s ##############" % cls )

	def setUp( self ):
		self.s = Sequitur()

	def test_sequitur_run( self ):
		print
		data = list("abcdbcabcd")
		for x in data:
			self.s.append( x )
			print self.s
			print "--"

#########################################################################################
if __name__ == '__main__':
    unittest.main()


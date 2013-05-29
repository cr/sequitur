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
		log.basicConfig( level=log.DEBUG )
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
		n = 1
		a = Symbol( n )
		self.assertTrue( isinstance( a, Symbol ) )
		self.assertFalse( a.is_connected() )
		self.assertIs( a.next, a )
		self.assertIs( a.prev, a )
		self.assertIs( a.ref, n )

	def test_symbol_is_connected( self ):
		a = Symbol( 1 )
		b = Symbol( 2 )
		self.assertFalse( a.is_connected() )
		self.assertFalse( b.is_connected() )
		a.insertnext( b )
		self.assertTrue( a.is_connected() )
		self.assertTrue( b.is_connected() )

	def test_symbol_is_guard( self ):
		r = Rule()
		g = r.guard
		a = Symbol( 1 )
		self.assertTrue( g.is_guard() )
		self.assertFalse( a.is_guard() )

	def test_symbol_linkage( self ):
		a = Symbol( 1 )
		b = Symbol( 2 )
		self.assertIs( a.next, a )
		self.assertIs( a.prev, a )
		self.assertIs( b.next, b )
		self.assertIs( b.prev, b )
		a.insertnext( b )
		self.assertIs( a.next, b )
		self.assertIs( a.prev, b )
		self.assertIs( b.next, a )
		self.assertIs( b.prev, a )

	def test_symbol_digrams( self ):
		g = Symbol( Symbol ( 0 ) )
		a = Symbol( 1 )
		b = Symbol( 2 )
		g.insertnext( a )
		a.insertnext( b )
		self.assertEqual( a.digram(), (a,b) )
		self.assertEqual( a.refdigram(), (1,2) )
		with self.assertRaises( SymbolError ): g.digram()
		with self.assertRaises( SymbolError ): b.digram()

	def test_symbol_replace_digram( self ):
		a = Symbol( 1 )
		b = Symbol( 2 )
		c = Symbol( 3 )
		d = Symbol( 4 )
		e = Symbol( 5 )
		a.insertnext( b )
		b.insertnext( c )
		c.insertnext( d )
		ret = b.replace_digram( e )
		self.assertIs( ret.ref, e )
		self.assertIs( a.next, ret )
		self.assertIs( ret.next, d )
		self.assertIs( d.next, a )
		self.assertIs( d.prev, ret )
		self.assertIs( ret.prev, a )
		self.assertIs( a.prev, d )

	def test_symbol_replace_symbol( self ):
		r = Rule()
		a = r.append( 1 )
		b = r.append( 2 )
		c = r.append( 3 )
		d = r.append( 4 )
		s = Rule()
		e = s.append( 5 )
		f = s.append( 6 )
		tail, head = b.replace_symbol( s )
		self.assertIs( tail, e )
		self.assertIs( head, f )
		self.assertIs( r.guard.next, a )
		self.assertIs( a.next, e )
		self.assertIs( e.next, f )
		self.assertIs( f.next, c )
		self.assertIs( c.next, d )
		self.assertIs( d.next, r.guard )
		self.assertIs( r.guard.prev, d )
		self.assertIs( d.prev, c )
		self.assertIs( c.prev, f )
		self.assertIs( f.prev, e )
		self.assertIs( e.prev, a )
		self.assertIs( a.prev, r.guard )
		#TODO: test replacing next to guards

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
		self.assertTrue( r.is_empty )
		self.assertTrue( r.guard.is_guard() )
		self.assertIs( r.guard.ref.ref, r )
		self.assertIs( r.guard.next, r.guard )
		self.assertIs( r.guard.prev, r.guard )
		self.assertEqual( r.refcount(), 0 )

	def test_rule_delete( self ):
		r = Rule()
		r.delete()
		r = Rule()
		a = r.append( 1 )
		with self.assertRaises( RuleError ): r.delete()

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

	def test_rule_is_empty( self ):
		r = Rule()
		self.assertTrue( r.is_empty() )
		r.append( 1 )
		self.assertFalse( r.is_empty() )

	def test_rule_refcount( self ):
		r = Rule()
		self.assertEqual( r.refcount(), 0 )
		a = Symbol( r )
		self.assertEqual( r.refcount(), 1 )
		b = Symbol( r )
		self.assertEqual( r.refcount(), 2 )
		c = Symbol( r )
		self.assertEqual( r.refcount(), 3 )
		b.delete()
		self.assertEqual( r.refcount(), 2 )

	def test_rule_each( self ):
		r = Rule()
		a = r.append( 1 )
		b = r.append( 2 )
		self.assertEqual( [ref for ref in r.each()], [1,2] )
		self.assertEqual( [ref for ref in r.eachsymbol()], [a,b] )

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

	def test_rule_replace_lastref( self ):
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
		d = Symbol( r )
		self.assertEqual( r.refcount(), 2 )
		d.delete() # should trigger killref/replace_lastref/delete cascade
		# CAVE: r is now an invalid rule
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
		with self.assertRaises( SymbolError ): index.key( b ) # b.next is a guard
		with self.assertRaises( SymbolError ): index.key( r.guard )

	def test_index_learning( self ):
		# temporarily disable makeunique to prevent failure on low-level linkage
		tmpmakeunique = Rule.makeunique
		Rule.makeunique = Rule.makeunique_disabled
		# calls to learn() and forget() are implicit through symbol linkage/unlinkage
		unlearned = Symbol( 1 )
		unlearnedb = Symbol( 2 )
		unlearned.insertnext( unlearnedb )
		self.assertFalse( index.seen( unlearned ) )
		a = Symbol( 1 )
		b = Symbol( 2 )
		a.insertnext( b )
		self.assertFalse( index.seen( unlearned ) )
		index.learn( a )
		self.assertTrue( index.seen( unlearned ) )
		self.assertIs( index.seen( unlearned ), a )
		self.assertTrue( index.seen( a ) )
		index.forget( a )
		self.assertFalse( index.seen( unlearned ) )

		r = Rule()
		c = r.append( 1 )
		with self.assertRaises( SymbolError ): index.seen( c.prev ) # c.prev is guard
		with self.assertRaises( SymbolError ): index.seen( c ) # c.next is guard
		d = r.append( 1 )
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
		self.assertEqual( len(s.refs), 2 )
		self.assertTrue( r.guard.next.next in s.refs )
		self.assertTrue( r.guard.next.next.next.next in s.refs )
		#print "2#######################"
		#print_state()
		r.append( 1 )
		self.assertEqual( r.dump(), [1,s,4,s,1] )
		self.assertEqual( s.dump(), [2,3] )
		self.assertEqual( r.walk(), [1,2,3,4,2,3,1] )
		self.assertEqual( len(s.refs), 2 )
		self.assertTrue( r.guard.next.next in s.refs )
		self.assertTrue( r.guard.next.next.next.next in s.refs )
		#print "3#######################"
		#print_state()
		r.append( 2 )
		self.assertEqual( r.dump(), [1,s,4,s,1,2] )
		self.assertEqual( s.dump(), [2,3] )
		self.assertEqual( r.walk(), [1,2,3,4,2,3,1,2] )
		self.assertEqual( len(s.refs), 2 )
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


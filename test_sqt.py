#!/usr/bin/env python

from sqt import *
import unittest
import logging as log
log.basicConfig( level=log.DEBUG )
from IPython import embed

#########################################################################################
class Test_AA_Symbol( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.DEBUG )
		log.info( " ##### BEGIN %s ##############################################" % cls )
		# temporarily disable makeunique to leftent failure on low-level linkage
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
		self.assertIs( a.r, a )
		self.assertIs( a.l, a )
		self.assertIs( a.ref, n )

	def test_symbol_is_connected( self ):
		a = Symbol( 1 )
		b = Symbol( 2 )
		self.assertFalse( a.is_connected() )
		self.assertFalse( b.is_connected() )
		a.insertright( b )
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
		self.assertIs( a.r, a )
		self.assertIs( a.l, a )
		self.assertIs( b.r, b )
		self.assertIs( b.l, b )
		a.insertright( b )
		self.assertIs( a.r, b )
		self.assertIs( a.l, b )
		self.assertIs( b.r, a )
		self.assertIs( b.l, a )

	def test_symbol_digrams( self ):
		g = Symbol( Symbol ( 0 ) )
		a = Symbol( 1 )
		b = Symbol( 2 )
		g.insertright( a )
		a.insertright( b )
		self.assertEqual( a.digram(), (a,b) )
		self.assertEqual( a.refdigram(), (1,2) )
		#with self.assertRaises( SymbolError ): g.digram()
		#with self.assertRaises( SymbolError ): b.digram()

	def test_symbol_replace_digram( self ):
		a = Symbol( 1 )
		b = Symbol( 2 )
		c = Symbol( 3 )
		d = Symbol( 4 )
		e = Symbol( 5 )
		a.insertright( b )
		b.insertright( c )
		c.insertright( d )
		ret = b.replace_digram( e )
		self.assertIs( ret.ref, e )
		self.assertIs( a.r, ret )
		self.assertIs( ret.r, d )
		self.assertIs( d.r, a )
		self.assertIs( d.l, ret )
		self.assertIs( ret.l, a )
		self.assertIs( a.l, d )

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
		self.assertIs( r.guard.r, a )
		self.assertIs( a.r, e )
		self.assertIs( e.r, f )
		self.assertIs( f.r, c )
		self.assertIs( c.r, d )
		self.assertIs( d.r, r.guard )
		self.assertIs( r.guard.l, d )
		self.assertIs( d.l, c )
		self.assertIs( c.l, f )
		self.assertIs( f.l, e )
		self.assertIs( e.l, a )
		self.assertIs( a.l, r.guard )
		#TODO: test replacing right to guards

#########################################################################################
class Test_BA_Rule( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.ERROR )
		log.info( " ##### BEGIN %s ##############################################" % cls )
		# temporarily disable makeunique to leftent failure on low-level linkage
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
		self.assertIs( r.guard.r, r.guard )
		self.assertIs( r.guard.l, r.guard )
		self.assertEqual( r.refcount(), 0 )

	def test_rule_delete( self ):
		r = Rule()
		r.delete()
		r = Rule()
		a = r.append( 1 )
		#with self.assertRaises( RuleError ): r.delete()

	def test_rule_append( self ):
		r = Rule()
		a = r.append( 1 )
		self.assertTrue( r.guard.is_guard() )
		self.assertTrue( isinstance( a, Symbol ) )
		self.assertIs( r.guard.r, a )
		self.assertIs( r.guard.r.r, r.guard )
		self.assertIs( r.guard.l, a )
		self.assertIs( r.guard.l.l, r.guard )
		b = r.append( 2 )
		self.assertIs( r.guard.r, a )
		self.assertIs( r.guard.r.r, b )
		self.assertIs( r.guard.r.r.r, r.guard )
		self.assertIs( r.guard.l, b )
		self.assertIs( r.guard.l.l, a )
		self.assertIs( r.guard.l.l.l, r.guard )

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
		self.assertEqual( r.dump(), [1, 2] )
		self.assertEqual( r.walk(), [1, 2] )
		self.assertEqual( s.dump(), [3, r, 4] )
		self.assertEqual( s.walk(), [3, 1, 2, 4] )

	def test_rule_replace_digram( self ):
		r = Rule()
		r.append( 1 )
		r.append( 2 )
		s = Rule()
		a = s.append( 1 )
		b = s.append( 2 )
		c = s.append( 1 )
		d = s.append( 2 )
		e = s.append( 3 )
		f = s.append( 11 )
		g = s.append( 22 )
		anew = r.replace_digram( a )
		self.assertEqual( s.dump(), [r, 1, 2, 3, 11, 22] )
		cnew = r.replace_digram( c )
		self.assertEqual( s.dump(), [r, r, 3, 11, 22] )
		fnew = r.replace_digram( f )
		self.assertIs( anew, e.l.l )
		self.assertIs( cnew, e.l )
		self.assertIs( fnew, e.r )
		self.assertEqual( s.dump(), [r, r, 3, r] )
		self.assertEqual( s.walk(), [1, 2, 1, 2, 3, 1, 2] )
		self.assertEqual( r.dump(), [1, 2] )
		self.assertEqual( r.refcount(), 3 )
		self.assertTrue( anew in r.refs )
		self.assertTrue( cnew in r.refs )
		self.assertTrue( fnew in r.refs )
		#with self.assertRaises( SymbolError ): r.replace_digram( fnew )

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
		#with self.assertRaises( SymbolError ): index.key( b ) # b.r is a guard
		#with self.assertRaises( SymbolError ): index.key( r.guard )

	def test_index_learning( self ):
		# temporarily disable makeunique to leftent failure on low-level linkage
		tmpmakeunique = Rule.makeunique
		Rule.makeunique = Rule.makeunique_disabled
		# calls to learn() and forget() are implicit through symbol linkage/unlinkage
		unlearned = Symbol( 1 )
		unlearned.insertright( Symbol( 2 ) )
		self.assertFalse( index.seen( unlearned ) )
		a = Symbol( 1 )
		b = Symbol( 2 )
		a.insertright( b )
		self.assertFalse( index.seen( unlearned ) )
		index.learn( a )
		self.assertTrue( index.seen( unlearned ) )
		self.assertIs( index.seen( unlearned ), a )
		self.assertTrue( index.seen( a ) )
		index.forget( a )
		self.assertFalse( index.seen( unlearned ) )

		r = Rule()
		c = r.append( 1 )
		#with self.assertRaises( SymbolError ): index.seen( c.l ) # c.l is guard
		#with self.assertRaises( SymbolError ): index.seen( c ) # c.r is guard
		d = r.append( 1 )
		self.assertFalse( index.seen( unlearned ) )
		e = r.append( 2 )
		self.assertTrue( index.seen( unlearned ) )

		Rule.makeunique = tmpmakeunique

	def test_index_overlap( self ):
		unlearned = Symbol( 1 )
		unlearned.insertright( Symbol( 1 ) )
		a = Symbol( 1 )
		b = Symbol( 1 )
		c = Symbol( 1 )
		a.insertright( b )
		b.insertright( c )
		self.assertFalse( index.seen( unlearned ) )
		index.learn( a )
		self.assertIs( index.seen( unlearned ), a )
		index.learn( b )
		self.assertIs( index.seen( unlearned ), b )

	def test_index_killref( self ):
		#TODO: simplify to the point
		r = Rule()
		r.append( 1 )
		r.append( 2 )
		r.append( 3 )
		r.append( 4 )
		r.append( 2 )
		self.assertEqual( len(Rule.rules), 1 )
		self.assertIs( Rule.rules[0], r )
		self.assertEqual( r.walk(), [1,2,3,4,2] )
		r.append( 3 )
		self.assertEqual( len(Rule.rules), 2 )
		s = Rule.rules[1]
		self.assertEqual( r.dump(), [1,s,4,s] )
		self.assertEqual( s.dump(), [2,3] )
		self.assertEqual( r.walk(), [1,2,3,4,2,3] )
		self.assertEqual( len(s.refs), 2 )
		self.assertTrue( r.guard.r.r in s.refs )
		self.assertTrue( r.guard.r.r.r.r in s.refs )
		r.append( 1 )
		self.assertEqual( r.dump(), [1,s,4,s,1] )
		self.assertEqual( s.dump(), [2,3] )
		self.assertEqual( r.walk(), [1,2,3,4,2,3,1] )
		self.assertEqual( len(s.refs), 2 )
		self.assertTrue( r.guard.r.r in s.refs )
		self.assertTrue( r.guard.r.r.r.r in s.refs )
		r.append( 2 )
		self.assertEqual( r.dump(), [1,s,4,s,1,2] )
		self.assertEqual( s.dump(), [2,3] )
		self.assertEqual( r.walk(), [1,2,3,4,2,3,1,2] )
		self.assertEqual( len(s.refs), 2 )
		self.assertTrue( r.guard.r.r in s.refs )
		#elf.assertTrue( r.guard.r.r.r.r in s.refs )
		r.append( 3 )
		#print_state()
		#self.assertEqual( len(Rule.rules), 3 )
		#self.assertFalse( 1 in Rule.rules )
		#t = Rule.rules[2]
		#self.assertEqual( r.dump(), [t,4,2,3,t] )
		#self.assertEqual( t.dump(), [1,2,3] )
		#self.assertTrue( r.guard.r in t.refs )
		#self.assertTrue( r.guard.r.r.r.r.r in t.refs )
		r.append( 4 )
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
		index.reset()
		Rule.reset()

	def test_sequitur_run( self ):
		print
		self.s = Sequitur()
		data = list("abcdbcabcd")
		for x in data:
			self.s.append( x )
			print self.s
			print "--"

	def test_sequitur_overlaping_left_issue( self ): 
		# if on overlap you only learn the right-hand digram,
		# the following situation as described in the comments will occurr
		r = Rule()
		r.append( 1 )
		r.append( 2 )
		a = r.append( 2 ) # 2,2 is learned
		r.append( 2 ) # second 2,2 digram will not be learned because of overlap
		r.append( 1 )
		print_state()
		#embed()
		r.append( 2 ) # 1,2 becomes new rule r, both instances are replaced
		              # 2,2 unlearned because of broken connecttion (BUG), while S=r,2,2,r
		self.assertIs( index.seen( a ), a )
		r.append( 2 ) # the old and new r,2 is replaced by rule s, S=s,2,s
		              # 2,2 is unlearned, but not in index, resulting in KeyError

	def test_sequitur_other_overlaping_right_issue( self ): 
		# for the same reason as above, the symmetric problem occurs if
		# only the right-hand side of overlapping digrams is learned:
		r = Rule()
		r.append( 1 )
		print_state()
		r.append( 2 )
		print_state()
		r.append( 3 ) # 2,3 learned
		print_state()
		r.append( 2 )
		print_state()
		r.append( 2 ) # 2,2 learned
		print_state()
		r.append( 2 ) # overlapping 2,2 overrides leftious
		print_state()
		r.append( 3 ) # 2,2 unlearned because of rule substitution, but still in index (BUG)
		print_state()
		r.append( 1 )
		print_state()
		r.append( 2 )
		print_state()
		r.append( 3 )
		print_state()
		r.append( 2 ) # crash with KeyError
		print_state()

	def test_sequitur_overlapping_more( self ):
		#aaaabaaaaaa
		r = Rule()
		r.append( 1 )
		print_state()
		r.append( 1 )
		print_state()
		r.append( 1 )
		print_state()
		r.append( 1 )
		print_state()
		r.append( 2 )
		print_state()
		r.append( 1 )
		print_state()
		r.append( 1 )
		print_state()
		r.append( 1 )
		print_state()
		r.append( 1 )
		print_state()
		r.append( 1 )
		print_state()
		embed()
		r.append( 1 )
		print_state()


	# This test should be in TestRule, but the class has the
	# Rule.makeunique trigger globally disabled
	def test_sequitur_makeunique( self ):
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


#########################################################################################
if __name__ == '__main__':
    unittest.main()


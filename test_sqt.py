#!/usr/bin/env python

from sqt import *
import random
import unittest
import logging as log
log.basicConfig( level=log.DEBUG )
from IPython import embed


# global callback return variable
cb = []
def callback( *args, **kw ):
	global cb
	cb.append( ( args, kw ) )

#########################################################################################
class Test_AA_Symbol( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.DEBUG )
		log.info( " ##### BEGIN %s ##############################################" % cls )

	@classmethod
	def tearDownClass( cls ):
		log.info( " ##### END %s ##############" % cls )

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
		a.insert( b )
		self.assertTrue( a.is_connected() )
		self.assertTrue( b.is_connected() )

	def test_symbol_is_guard( self ):
		a = Symbol( 1 )
		self.assertFalse( a.is_guard() )

	def test_symbol_linkage( self ):
		a = Symbol( 1 )
		b = Symbol( 2 )
		self.assertIs( a.r, a )
		self.assertIs( a.l, a )
		self.assertIs( b.r, b )
		self.assertIs( b.l, b )
		a.insert( b )
		self.assertIs( a.r, b )
		self.assertIs( a.l, b )
		self.assertIs( b.r, a )
		self.assertIs( b.l, a )

	def test_symbol_digrams( self ):
		g = Symbol( Symbol ( 0 ) )
		a = Symbol( 1 )
		b = Symbol( 2 )
		g.insert( a )
		a.insert( b )
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
		a.insert( b )
		b.insert( c )
		c.insert( d )
		ret = b.replace_digram( e )
		self.assertIs( ret, e )
		self.assertIs( d.r, a )
		self.assertIs( d.l, ret )
		self.assertIs( a.l, d )

#########################################################################################
class Test_BB_Ruleref( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.ERROR )
		log.info( " ##### BEGIN %s ##############################################" % cls )

	@classmethod
	def tearDownClass( cls ):
		Rule.reset()
		log.info( " ##### END %s ##############" % cls )

	def setUp( self ):
		Rule.reset()

	def test_ruleref_instance( self ):
		r = Rule()
		a = Ruleref( r )
		self.assertTrue( isinstance( a, Ruleref ) )
		self.assertFalse( a.is_connected() )
		b = Ruleref( r, ruleref=False )
		self.assertFalse( b in r.refs )
		c = Symbol( 1 )
		a.insert( c )
		self.assertTrue( a.is_connected() )

	def test_ruleref_replace( self ):
		r = Rule()
		e = r.append( 2 )
		f = r.append( 3 )
		s = Rule()
		a = s.append( r )
		b = s.append( r )
		c = s.append( r )
		tail, head = a.replace()
		self.assertIs( tail, e )
		self.assertIs( head, f )
		self.assertEqual( s.dump(), [2,3,r,r] )
		#TODO: test overlap conditions

	def test_ruleref_refs( self ):
		r = Rule()
		self.assertEqual( r.refcount(), 0 )
		a = Ruleref( r )
		self.assertEqual( r.refcount(), 1 )
		self.assertTrue( a in r.refs )
		b = Ruleref( r )
		self.assertEqual( r.refcount(), 2 )
		self.assertTrue( b in r.refs )
		c = Ruleref( r )
		self.assertEqual( r.refcount(), 3 )
		self.assertTrue( c in r.refs )
		b.delete() # triggers killref
		self.assertEqual( r.refcount(), 2 )
		self.assertTrue( a in r.refs )
		self.assertFalse( b in r.refs )
		self.assertTrue( c in r.refs )

	def test_ruleref_delete( self ):
		r = Rule()
		a = r.append( 1 )
		b = r.append( 2 )
		s = Rule()
		c = s.append( r )
		d = s.append( 3 )
		e = Ruleref( r )
		e.delete() # triggers killref
		self.assertEqual( s.dump(), [1,2,3] )

#########################################################################################
class Test_BA_Rule( unittest.TestCase ):

	@classmethod
	def setUpClass( cls ):
		log.basicConfig( level=log.ERROR )
		log.info( " ##### BEGIN %s ##############################################" % cls )

	@classmethod
	def tearDownClass( cls ):
		Rule.reset()
		log.info( " ##### END %s ##############" % cls )

	def setUp( self ):
		Rule.reset()

	def test_rule_instance( self ):
		r = Rule()
		self.assertTrue( isinstance( r, Rule ) )
		self.assertTrue( r.is_empty() )
		self.assertTrue( r.guard.is_guard() )
		self.assertIs( r.guard.ref, r )
		self.assertIs( r.guard.r, r.guard )
		self.assertIs( r.guard.l, r.guard )
		self.assertEqual( r.refcount(), 0 )

	def test_rule_rulemarker( self ):
		#TODO
		pass

	def test_rule_delete( self ):
		r = Rule()
		r.delete()
		r = Rule()
		a = r.append( 1 )
		with self.assertRaises( RuleError ): r.delete()

	def test_rule_append( self ):
		r = Rule()
		a = r.append( 1 )
		b = r.append( 2 )
		self.assertEqual( r.guard.r.digram(), (a,b) )
		self.assertEqual( a.digram(), (a,b) )
		c = r.append( r  )
		self.assertIs( c.ref, r )
		with self.assertRaises( SymbolError ): c.digram()

	def test_rule_is_empty( self ):
		r = Rule()
		self.assertTrue( r.is_empty() )
		r.append( 1 )
		self.assertFalse( r.is_empty() )

	def test_rule_each( self ):
		r = Rule()
		self.assertEqual( [ref for ref in r.each()], [] )
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

	def test_rule_dissolve( self ):
		global cb
		r = Rule()
		beginning = r.append( 1 )
		r.append( 2 )
		middle = r.append( 1 )
		r.append( 2 )
		end = r.append( 1 )
		r.append( 2 )
		newmiddle    = r.dissolve( middle, forget=False )
		newbeginning = r.dissolve( beginning, forget=False )
		newend       = r.dissolve( end )
		self.assertEqual( [s for s in r.eachsymbol()], [newbeginning, newmiddle, newend] ) 
		self.assertEqual( r.dump(), [r,r,r] )
		#TODO: test overlap conditions

	def test_rule_dissolve( self ):
		r = Rule()
		r.append( 1 )
		r.append( 2 )
		s = Rule()
		s.append( r )
		s.append( 1 )
		#TODO: test overlap conditions

	def _test_rule_known_dissolve_failmode( self ):
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
		anew = r.dissolve( a ) # broken here. no reference
		self.assertEqual( s.dump(), [r, 1, 2, 3, 11, 22] )
		cnew = r.dissolve( c )
		self.assertEqual( s.dump(), [r, r, 3, 11, 22] )
		fnew = r.dissolve( f )
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
		#with self.assertRaises( SymbolError ): r.dissolve( fnew )

	def _test_rule_dissolve_failmode( self ):
		r = Rule()
		r.append( 1 )
		r.append( 2 )
		s = Rule()
		a = s.append( 3 )
		b = s.append( 1 )
		c = s.append( 2 )
		ret = r.dissolve( b )
		self.assertEqual( r.refcount(), 1 )
		self.assertTrue( ret in r.refs )
		d = Symbol( r )
		self.assertEqual( r.refcount(), 2 )
		d.delete() # should trigger killref/dissolve/delete cascade
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
		Rule.reset()
		log.info( " ##### END %s ##############" % cls )

	def setUp( self ):
		self.index = Index()
		Rule.reset()

	def test_index_instance( self ):
		self.assertTrue( isinstance( self.index, Index ) )
		self.assertEqual( len(self.index.dict), 0 )

	def test_index_keys( self ):
		# TODO: test with more datatypes
		# TODO: test with rule references
		a = Symbol( 1 )
		b = Symbol( 2 )
		a.insert( b )
		self.assertEqual( self.index.key( a ), "1"+self.index.keyseparator+"2" )
		self.index.reset( keyseparator="foo" )
		self.assertEqual( self.index.key( a ), "1foo2" )
		self.assertEqual( self.index.key( a ), "1"+self.index.keyseparator+"2" )
		self.index.reset()
		self.assertEqual( self.index.key( a ), "1"+self.index.keyseparator+"2" )
		#with self.assertRaises( SymbolError ): self.index.key( b ) # b.r is a guard
		#with self.assertRaises( SymbolError ): self.index.key( r.guard )

	def test_index_learning( self ):
		# calls to learn() and forget() are implicit through symbol linkage/unlinkage
		unlearned = Symbol( 1 )
		unlearned.insert( Symbol( 2 ) )
		self.assertFalse( self.index.seen( unlearned ) )
		a = Symbol( 1 )
		a.insert( Symbol( 2 ) )
		self.assertFalse( self.index.seen( unlearned ) )
		self.index.learn( a )
		self.assertTrue( self.index.seen( unlearned ) )
		self.assertIs( self.index.seen( unlearned ), a )
		self.assertTrue( self.index.seen( a ) )
		self.index.forget( a )
		self.assertFalse( self.index.seen( unlearned ) )
		#TODO: test overlap conditions

	def test_index_overlap( self ):
		global cb
		a = Symbol( 1 )
		b = Symbol( 1 )
		c = Symbol( 1 )
		d = Symbol( 1 )
		a.insert( b )
		b.insert( c )
		c.insert( d )
		cb = []
		self.index.learn( a, makeunique=callback )
		self.assertEqual( len(cb), 0 )
		self.index.learn( b, makeunique=callback )
		self.assertEqual( len(cb), 0 )
		self.index.learn( c, makeunique=callback )
		self.assertEqual( len(cb), 1 )
		args,kw = cb.pop()
		self.assertEqual( args, (a,c) )

	def test_index_makeunique( self ):
		global cb
		a = Symbol( 1 )
		b = Symbol( 2 )
		c = Symbol( 1 )
		d = Symbol( 2 )
		a.insert( b )
		b.insert( c )
		c.insert( d )
		cb = []
		self.index.learn( a, makeunique=callback )
		self.assertEqual( len(cb), 0 )
		self.index.learn( c, makeunique=callback )
		self.assertEqual( len(cb), 1 )
		args,kw = cb.pop()
		self.assertEqual( args, (a,c) )

		#self.assertFalse( 1 in Rule.rules )
		#t = Rule.rules[2]
		#self.assertEqual( r.dump(), [t,4,2,3,t] )
		#self.assertEqual( t.dump(), [1,2,3] )
		#self.assertTrue( r.guard.r in t.refs )
		#self.assertTrue( r.guard.r.r.r.r.r in t.refs )
		#r.append( 4 )
		#self.assertEqual( r.walk(), [1, 2, 3, 4, 2, 3, 1, 2, 3, 4] )

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

	def test_sequitur_paperseq( self ):
		data = list( "abcdbcabcd" )
		for x in data:
			self.s.append( x )
			#print_state( self.s.index )
		S = Rule.rules['r0']
		A = Rule.rules['r1']
		with self.assertRaises( KeyError ): B = Rule.rules['r2']
		C = Rule.rules['r3']
		self.assertEqual( S.dump(), [C,A,C] )
		self.assertEqual( A.dump(), ['b','c'] )
		self.assertEqual( C.dump(), ['a',A,'d'] )
		self.assertEqual( [x for x in self.s.walk()], data )

	def test_sequitur_overlapping_left_issue( self ): 
		# if on overlap you only learn the right-hand digram,
		# the following situation as described in the comments will occurr
		#r = Rule()
		#r.append( 1 )
		#r.append( 2 )
		#a = r.append( 2 ) # 2,2 is learned
		#r.append( 2 ) # second 2,2 digram will not be learned because of overlap
		#r.append( 1 )
		#embed()
		#r.append( 2 ) # 1,2 becomes new rule r, both instances are replaced
		               # 2,2 unlearned because of broken connecttion (BUG), while S=r,2,2,r
		#self.assertIs( self.s.index.seen( a ), a )
		#r.append( 2 ) # the old and new r,2 is replaced by rule s, S=s,2,s
		               # 2,2 is unlearned, but not in index, resulting in KeyError
		data = list( "abbbabb" )
		for x in data:
			self.s.append( x )
			#print_state( self.s.index )	

	def test_sequitur_overlapping_right_issue( self ): 
		# for the same reason as above, the symmetric problem occurs if
		# only the right-hand side of overlapping digrams is learned:
		#self.s.append( 1 )
		#self.s.append( 2 )
		#self.s.append( 3 ) # 2,3 learned
		#self.s.append( 2 )
		#self.s.append( 2 ) # 2,2 learned
		#self.s.append( 2 ) # overlapping 2,2 overrides leftious
		#self.s.append( 3 ) # 2,2 unlearned because of rule substitution, but still in index (BUG)
		#self.s.append( 1 )
		#self.s.append( 2 )
		#self.s.append( 3 )
		#self.s.append( 2 ) # crash with KeyError
		data = list( "abcbbbcabcb" )
		for x in data:
			self.s.append( x )
			#print_state( self.s.index )

	def test_sequitur_eternal_overlapping( self ):
		data = list( "aaaabaaaaaa" )
		for x in data:
			self.s.append( x )
			#print_state( self.s.index )

	def test_sequitur_double_crash( self ):
		data = list( "aabbaabb" )
		for x in data:
			self.s.append( x )
			#print_state( self.s.index )

	def _test_sequitur_fuzz( self ):
		def rndstring():
			s = ""
			for b in xrange( 0, 50 ):
				char = chr( random.randint( 0, 3 ) + ord( 'a' ) )
				rep = random.randint( 1, 5 )
				s += char*rep
			return s
		log.basicConfig( level=log.WARNING )
		for x in xrange( 2000 ):
			s = Sequitur()
			rnd = list( rndstring() )
			for c in rnd: s.append( c )
			self.assertEqual( [x for x in s.walk()], rnd )


#########################################################################################
if __name__ == '__main__':
    unittest.main()


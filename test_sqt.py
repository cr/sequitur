#!/usr/bin/env python

from sqt import *
import unittest

class SymbolTest( unittest.TestCase ):

	def setUp( self ):
		# build a rule: guard <-> a:1 <-> b:2 <-> guard
		self.b = Symbol( 2 )
		self.a = Symbol( 1, next=self.b )
		self.guard = Symbol( None, next=self.a, prev=self.b )
		self.b.next = self.guard
		self.b.prev = self.a
		self.a.prev = self.guard
		self.floatingguard = Symbol()

	def test_symbol_instances( self ):
		self.assertTrue( isinstance( self.guard, Symbol ) )
		self.assertTrue( isinstance( self.a, Symbol ) )
		self.assertTrue( isinstance( self.b, Symbol ) )
		self.assertTrue( isinstance( self.a.next, Symbol ) )
		self.assertTrue( isinstance( self.b.prev, Symbol ) )
		self.assertTrue( isinstance( self.floatingguard, Symbol ) )

	def test_symbol_types( self ):
		self.assertTrue( self.guard.is_guard() )
		self.assertFalse( self.a.is_guard() )

	def test_symbol_values( self ):
		self.assertEqual( self.guard.ref, None )
		self.assertEqual( self.a.ref, 1 )
		self.assertEqual( self.b.ref, 2 )
		self.assertEqual( self.floatingguard.ref, None )

	def test_symbol_linkage( self ):
		self.assertIs( self.guard.next, self.a )
		self.assertIs( self.a.next, self.b )
		self.assertIs( self.b.next, self.guard )
		self.assertIs( self.guard.prev, self.b )
		self.assertIs( self.a.prev, self.guard )
		self.assertIs( self.b.prev, self.a )
		self.assertIs( self.guard.next.next.next, self.guard )
		self.assertIs( self.guard.prev.prev.prev, self.guard )
		self.assertIs( self.floatingguard.next, None )
		self.assertIsNot( self.guard.next, self.b )

	def test_symbol_pointers( self ):
		self.assertIs( self.a.next.next.next, self.a )
		self.assertEqual( self.a.next.next.next.ref, self.a.ref )
		self.assertIs( self.a.prev.prev.prev, self.a )
		self.assertEqual( self.a.prev.prev.prev.ref, self.a.ref )

	def test_symbol_floating_exception( self ):
		with self.assertRaises( AttributeError ): self.floatingguard.next.next
		with self.assertRaises( AttributeError ): self.floatingguard.prev.prev

	def test_symbol_digrams( self ):
		self.assertEqual( self.guard.digram(), (None,1) ) 
		self.assertEqual( self.a.digram(), (1,2) ) 
		self.assertEqual( self.b.digram(), (2,None) )
		with self.assertRaises( AttributeError ): self.floatingguard.digram()

	def test_symbol_replace_digram( self ):
		# guard <-> floatingnonterminal <-> guard
		self.a.replace_digram( self.floatingguard )
		self.assertIs( self.guard.next, self.floatingguard )
		self.assertIs( self.guard.next.next, self.guard )
		self.assertIsNot( self.guard.prev, self.floatingguard )


class RuleTest( unittest.TestCase ):

	def setUp( self ):
		# ruleA <- guard <-> 1 <-> 2 -> guard
		self.ruleA = Rule()
		self.a = Symbol(1)
		self.b = Symbol(2)
		self.ruleA.append( self.a )
		self.ruleA.append( self.b )

		# ruleB <- guard <-> 3 <-> ruleA <-> 4 <-> ruleA <-> 5 -> guard
		self.ruleB = Rule()
		self.ruleB.append( 3 )
		self.ruleB.append( 1 )
		self.ruleB.append( 2 )
		self.ruleB.append( 4 )
		self.ruleB.append( 1 )
		self.ruleB.append( 2 )

		instanceA = self.ruleB.guard.next.next
		instanceB = self.ruleB.guard.next.next.next.next.next
		seenat = self.ruleA
		seenat.replace_digram( instanceA )
		seenat.replace_digram( instanceB )

		self.ruleB.append( 5 )

	def __test_rule_print( self ):
		print self.ruleA.dump()
		print self.ruleA.walk()
		print self.ruleB.dump()
		print self.ruleB.walk()

		print "ruleA nexts:", repr(self.ruleA.guard), repr(self.ruleA.guard.next), repr(self.ruleA.guard.next.next), repr(self.ruleA.guard.next.next.next)
		print "ruleA head:", repr(self.ruleA.head)

	def test_rule_instances( self ):
		self.assertTrue( isinstance( self.ruleA, Rule ) )
		self.assertTrue( isinstance( self.ruleB, Rule ) )
		self.assertTrue( self.ruleA.guard.is_guard() )
		self.assertFalse( self.ruleA.guard.next.is_guard() )
		self.assertTrue( self.ruleB.guard.is_guard() )

	def test_rule_linkage( self ):
		self.assertIs( self.ruleA.guard.next, self.a )
		self.assertIs( self.ruleA.guard.next.prev, self.ruleA.guard )
		self.assertIs( self.ruleA.guard.next.next, self.b )
		self.assertIs( self.ruleA.guard.next.next.prev, self.a )
		self.assertIs( self.ruleA.guard.next.next.prev.prev, self.ruleA.guard )
		self.assertIs( self.ruleA.guard.next.next.next, self.ruleA.guard )
		self.assertIs( self.ruleA.guard.next.next, self.ruleA.head )
		self.assertIs( self.ruleA.guard.prev, self.ruleA )

		self.assertIs( self.ruleB.guard.next.prev, self.ruleB.guard )
		self.assertIs( self.ruleB.guard.next.next.prev, self.ruleB.guard.next )
		self.assertIs( self.ruleB.guard.next.next.next.prev, self.ruleB.guard.next.next )
		self.assertIs( self.ruleB.guard.next.next.next.next.prev, self.ruleB.guard.next.next.next )
		self.assertIs( self.ruleB.guard.next.next.next.next.next.prev, self.ruleB.guard.next.next.next.next )
		self.assertIs( self.ruleB.guard.next.next.next.next.next.next, self.ruleB.guard )
		self.assertIs( self.ruleB.guard.next.next.ref, self.ruleA )
		self.assertIs( self.ruleB.guard.next.next.next.next.ref, self.ruleA )
		self.assertIs( self.ruleB.guard.next.next.next.next.next, self.ruleB.head )
		self.assertIs( self.ruleB.guard.prev, self.ruleB )

	def test_rule_output( self ):
		self.assertEqual( self.ruleA.dump(), [1, 2] )
		self.assertEqual( self.ruleA.walk(), [1, 2] )
		self.assertEqual( self.ruleB.dump()[0], 3 )
		self.assertTrue( isinstance( self.ruleB.dump()[1], Rule) )
		self.assertEqual( self.ruleB.dump()[2], 4 )
		self.assertEqual( self.ruleB.walk(), [3, 1, 2, 4, 1, 2, 5] )

	def test_rule_delete( self ):
		a = Rule()
		a.append( 1 )
		a.append( 2 )
		b = Rule()
		b.append( 3 )
		b.append( 1 )
		b.append( 2 )
		a.replace_digram( b.guard.next.next )
		self.assertEqual( a.refcount(), 1 )
		self.assertEqual( b.refcount(), 0 )
		self.assertEqual( b.dump(), [3,a] )
		a.delete()
		self.assertEqual( b.dump(), [3,1,2] )


class IndexText( unittest.TestCase ):

	def setUp( self ):
		self.index = Index()
		# rule: guard -> 1 -> 2 -> 2 -> 2 -> guard
		self.rule = Rule( 0 )
		self.rule.append( 1 )
		self.rule.append( 2 )
		self.rule.append( 2 )
		self.rule.append( 2 )
		
	def test_index_setup( self ):
		self.assertTrue( isinstance( self.index, Index ) )
		self.assertTrue( isinstance( self.rule, Rule ) )
		self.assertEqual( self.rule.id, 0 )
		self.assertEqual( self.rule.guard.next.ref, 1 )
		self.assertEqual( self.rule.guard.next.next.ref, 2 )
		self.assertIs( self.rule.guard.next.next.next.next.next, self.rule.guard )

	def test_index_keys( self ):
		# TODO: test with more datatypes
		# TODO: test with rule references
		self.assertEqual( Index.key( self.rule.guard.next ), "1"+Index.key_separator+"2" )
		with self.assertRaises( AttributeError ): Index.key( Symbol() )

	def test_index_learning( self ):
		symbol = self.rule.guard.next
		self.assertFalse( self.index.seen( symbol ) )
		self.index.learn( symbol, callbackifseen=(lambda *args, **kw: False) )
		self.assertTrue( self.index.seen( symbol ) )
		self.assertIs( self.index.seen( symbol ), symbol )


class SequiturTest( unittest.TestCase ):

	def setUp( self ):
		self.s = Sequitur()

	def test_sequitur_run( self ):
		print
		data = list("abcdbcabcd")
		for x in data:
			self.s.append( x )
			print self.s
		print self.s.walk()


if __name__ == '__main__':
    unittest.main()


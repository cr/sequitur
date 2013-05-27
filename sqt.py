#!/usr/bin/env python

import sys
from IPython import embed

class Symbol( object ):
	"""A helper class to faciliate pointer arithmetics"""

	def __init__(self, reference=None, next=None, prev=None ):
		self.ref = reference
		self.prev = prev
		self.next = next

	def is_guard( self ):
		return self.ref is None

	def digram( self ):
		return self.ref, self.next.ref

	def replace_digram( self, symbol ):
		if not isinstance( symbol, Symbol ):
			symbol = Symbol( symbol )
		prev = self.prev
		next = self.next
		nextnext = next.next
		symbol.next = nextnext
		symbol.prev = prev
		prev.next = symbol
		if not nextnext.is_guard(): nextnext.prev = symbol
		#del self.next.prev
		#del self.next
		return symbol

	def __str__( self ):
		return repr(self) + ":" + str( self.ref )


class Rule( object ):

	def __init__( self, id=None ):
		self.guard = Symbol( None )
		self.guard.next = self.guard
		self.guard.prev = self
		self.head = self.guard
		self.id = id
		self.refs = set()
		print "creating new rule", repr(self), self

	def delete( self ):
		assert len( self.refs ) == 1
		ref = self.refs.pop()
		print "deleting last", repr(self), str(self), "from", ref
		#embed() 
		# restore rule in place 
		#TODO: move functionality to Symbol class?
		prev = ref.prev
		next = ref.next
		tail = self.guard.next
		head = self.head
		prev.next = tail
		tail.prev = prev
		head.next = next
		if not next.is_guard():
			next.prev = head
		else:
			next.prev.head = head
		#del self.guard
		#del self.head
		#TODO: how to delete rule from Seqitur ruleset? #TODO: ##############################################################

	def append( self, symbol ):
		# wrap rule references (non-Symbol) in a Symbol
		if not isinstance( symbol, Symbol ):
			symbol = Symbol( symbol )
		symbol.next = self.guard
		symbol.prev = self.head
		self.head.next = symbol
		self.head = symbol
		print "appending", symbol, "to", self

	def refcount( self ):
		return len( self.refs )

	def killref( self, ref ):
		print "killing", ref, "from", self
		try:       #TODO: ##############################################uglyhack####################
			self.refs.remove( ref )
		except KeyError:
			print "WARNING, trying to kill unregistered ref", ref
		if self.refcount() == 1: self.delete()

	def replace_digram( self, digram ):
		# ensure rule utility
		a,b = digram, digram.next
		print "replacing digram", a, b, "with rule", self
		if isinstance( a.ref, Rule ): a.ref.killref( a )
		if isinstance( b.ref, Rule ): b.ref.killref( b )
		new = digram.replace_digram( self )
		# fix head if rule tail was replaced
		if digram.next.next.is_guard(): digram.next.next.prev.head = new
		# push reference
		self.refs.add( new )
		return new

	def each( self ):
		p = self.guard.next
		while not p is self.guard:
			#print p.ref
			yield p.ref
			p = p.next

	def eachsym( self ):
		p = self.guard.next
		while not p is self.guard:
			#print p.ref
			yield p
			p = p.next

	def dump( self ):
		return [ref for ref in self.each()]

	def walk( self ):
		result = []
		for ref in self.each():
			if isinstance( ref, Rule ):
				result.extend( ref.walk() )
			else:
				result.append( ref )
		return result

	def prettystring( self ):
		#address = str( repr( self ) ).split(' ')[-1][:-1]
		if self.refcount() > -1: #TODO: ###############################################uglyhack############################################
			s = repr(self) + " " + str( self ) + " (" + str(self.refcount()) + ") [" + ", ".join([str(x) for x in self.eachsym()]) + "]: refs: " + str( self.refs )
			return s
		else:
			return ""

	def __str__( self ):
		# TODO: beware of str(rule) <-> symbol ambiguity
		# solution: escaping of rule indicator in non-rule keys
		return 'r' + str( self.id ) + 'r'


class Index( object ):
	"""Class for speedy lookups of digram occurrence"""

	key_separator = ',' # beware of key ambiguity

	@classmethod
	def key( cls, symbol ):
		a,b = symbol.digram()
		return str( a ) + Index.key_separator + str( b )

	def __init__( self ):
		self.dict = {}

	def seen( self, symbol ):
		key = Index.key( symbol )
		try:
			seenat = self.dict[key]
			print "seen " + key + " at " + repr(seenat)
			return seenat
		except KeyError: # not seen
			return False

	def learn( self, symbol, callbackifseen ):
		"""creates a digram reference in the dictionary if digram is new, else callback"""

		#TODO: best place for this head/tail check?
		#a,b = symbol.digram()
		#if a is None or b is None: return False
		if symbol.is_guard() or symbol.next.is_guard(): return False

		seenat = self.seen( symbol )
		if seenat:
			if not seenat.next is symbol: # overlap test
				print "callback with", repr(seenat), repr(symbol)
				return callbackifseen( seenat, symbol )
			else:
				return False
		else:
			key = Index.key( symbol )
			print "learning", key, "at", repr(symbol)
			self.dict[key] = symbol
			return True

	def forget( self, symbol ):
		"""removes symbol digram from the dictionary"""
		key = Index.key( symbol )
		try:
			del self.dict[key]
			print "forgetting", key
		except KeyError:
			# special case (None,foo) was a guard node
			pass

	def __str__( self ):
		#s = ""
		#for key in self.dict:
		#	self.dict[key]
		return str( self.dict )

# Gloabl instance of the Index
index = Index()


class Sequitur( object ):

	def __init__( self ):
		self.rules = {}
		self.nextruleid = 0
		# create the main sequence rule
		S = self.createrule()
		assert S.id == 0

	def createrule( self ):
		rid = self.nextruleid
		rule = Rule( rid )
		self.rules[rid] = rule
		self.nextruleid += 1
		return rule

	def append( self, symbol ):
		self.push( 0, Symbol( symbol ) )

	def push( self, ruleid, symbol ):
		digram = self.rules[ruleid].head
		rule = self.rules[ruleid]
		rule.append( symbol )
		if digram.is_guard(): return # was empty rule
		index.learn( digram, callbackifseen=self.makeunique )

	def makeunique( self, old, new ):
		if old.prev.is_guard() and old.next.next.is_guard():
			# full rule match, re-use existing rule
			#print "re-using", old.prev.prev
			oldrule = old.prev.prev
			# forget digrams about to be broken
			index.forget( new.prev ) #TODO: what if first symbol in rule?
			index.forget( new.next ) #TODO: do we ever need this? what if last?
			# replace new instance with rule reference
			new = oldrule.replace_digram( new )
			index.learn( new.prev, callbackifseen=self.makeunique )
			index.learn( new, callbackifseen=self.makeunique )
			return False
		else:
			# create a new rule of the old digram
			#print "creating new rule out of", old.ref, old.next.ref
			print "a"
			index.forget( old )
			index.forget( old.prev ) #TODO: what if first symbol in rule?
			print "b"
			index.forget( old.next ) #TODO: what if last symbol in rule?
			print "c"
			index.forget( new.prev ) #TODO: what if first symbol in rule?
			print "d"
			index.forget( new.next ) #TODO: do we ever need this? what if last?
			print "f"
			newrule = self.createrule()
			newrule.append( old.ref ) # .ref ensures that symbol copy is used for rule
			newrule.append( old.next.ref )
			print "g"
			index.learn( newrule.guard.next, callbackifseen=self.makeunique )
			# forget digrams about to be broken

			# replace both instances with new rule reference
			old = newrule.replace_digram( old )
			print "h"
			index.learn( old, callbackifseen=self.makeunique )
			print "i"
			index.learn( old.prev, callbackifseen=self.makeunique )
			print "j"
			new = newrule.replace_digram( new )
			print "k"
			print "l"
			index.learn( new.prev, callbackifseen=self.makeunique )
			print "m"
			index.learn( new, callbackifseen=self.makeunique )
			return False

	def walk( self ):
		return self.rules[0].walk()

	def __str__( self ):
		s = "### Rules ###" 
		for rid in self.rules:
			s += '\n' + self.rules[rid].prettystring()
		s += "\n### Index ###"
		s += '\n' + str( index )
		s += "\n#############"
		return s

def main():
	try:
		filename = sys.argv[1]
	except:
		print "ERROR: no filename argument given"
		sys.exit(5)

	with open( filename ) as f:
		data = bytearray( f.read() )

	s = Sequitur()
	for byte in data:
		s.append( byte )

	print s

if __name__ == '__main__':
	main()

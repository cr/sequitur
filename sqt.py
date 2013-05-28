#!/usr/bin/env python

import sys
import gc
import logging as log
from IPython import embed

class Index( object ):
	"""Class for speedy lookups of digram occurrence"""

	def __init__( self ):
		self.dict = {}
		self.keyseparator = ','

	def key( self, symbol ):
		a,b = symbol.refdigram()
		return str( a ) + self.keyseparator + str( b )

	def reset( self, keyseparator=',' ):
		del self.dict
		gc.collect()
		self.dict = {}
		self.keyseparator = keyseparator
		log.debug( " index reset" )

	def seen( self, symbol ):
		key = self.key( symbol )
		try:
			seenat = self.dict[key]
			log.debug( " index has %s at %s" % (key, repr(seenat)) )
			return seenat
		except KeyError: # not seen
			return False

	def learn( self, symbol ):
		"""creates a digram reference in the dictionary if digram is new"""

		# If a digram contains a guard, return False
		# Removes detection logic from Symbol class
		if symbol.is_guard() or symbol.next.is_guard(): return False

		seenat = self.seen( symbol )
		if seenat and (not (seenat.next is symbol)) and (not (seenat is symbol.next)): # seen and not overlapping
			self.forget( symbol ) # else makeunique will get even more ugly
			tolearn = Rule.makeunique( seenat, symbol )
			if tolearn:
				self.learn( tolearn.guard.next ) #because makeunique probably made index forget
			return False
		else:
			key = self.key( symbol )
			log.debug( " index learning %s at %s" % (key, repr(symbol)) )
			self.dict[key] = symbol
			return True

	def forget( self, symbol ):
		"""removes symbol digram from the dictionary"""
		key = index.key( symbol )
		try:
			del self.dict[key]
			log.debug( " index forgets %s" % key )
		except KeyError:
			# ignore (guard,foo) or (foo,guard)
			pass

	def __str__( self ):
		return ( self.dict )

# Global instance of the Index
index = Index()

class Symbol( object ):
	"""A helper class to faciliate pointer arithmetics"""

	def __init__( self, reference, guard=False ):
		if guard:
			assert isinstance( reference, Rule )
			self.ref = Symbol( reference )
		else:
			self.ref = reference
		self.prev = None
		self.next = None
		log.debug( " new Symbol %s with reference to %s" % (repr(self), repr(reference)) )

	def is_guard( self ):
		return isinstance( self.ref, Symbol )

	def prevconnect( self, prev ):
		#log.debug( " prevconnect %s,%s" % (repr(prev)+str(prev),repr(self)+str(self)) )
		self.prev = prev
		prev.next = self
		index.learn( prev )

	def nextconnect( self, next ):
		#log.debug( " nextconnect %s,%s" % (repr(self)+str(self),repr(next)+str(next)) )
		self.next = next
		next.prev = self
		index.learn( self )

	def prevdisconnect( self ):
		#log.debug( " prevdisconnect %s,%s" % (repr(self.prev)+str(self.prev),repr(self)+str(self)) )
		index.forget( self.prev )
		#if self.prev == None: return
		del self.prev.next
		self.prev.next = None
		del self.prev
		self.prev = None

	def nextdisconnect( self ):
		#log.debug( " nextdisconnect %s,%s" % (repr(self)+str(self),repr(self.next)+str(self.next)) )
		index.forget( self )
		#if self.next == None: return
		del self.next.prev
		self.next.prev = None
		del self.next
		self.next = None

	def digram( self ):
		if self.is_guard(): a = None
		else: a = self
		if self.next.is_guard(): b = None
		else: b = self.next
		return a, b

	def refdigram( self ):
		if self.is_guard(): a = None
		else: a = self.ref
		if self.next == None or self.next.is_guard(): b = None
		else: b = self.next.ref
		return a, b

	def replace_digram( self, newsymbol ):
		assert isinstance( newsymbol, Symbol )
		prev = self.prev
		a,b = self.digram()
		next = b.next
		assert not b.is_guard()
		a.prevdisconnect()
		b.nextdisconnect()
		a.nextdisconnect()
		next.prevconnect( newsymbol )
		prev.nextconnect( newsymbol ) # connect last to avoid handling dangling digrams
		return newsymbol

	def replace_symbol( self, tail, head ):
		assert isinstance( tail, Symbol )
		assert isinstance( head, Symbol )
		prev = self.prev
		next = self.next
		if tail.prev != None: tail.prevdisconnect()
		if head.next != None: head.nextdisconnect()
		self.prevdisconnect()
		self.nextdisconnect()
		next.prevconnect( head )
		prev.nextconnect( tail ) # connect last to avoig dangling digrams

	def debugstring( self ):
		return repr(self) + ":" + str( self.ref )

	def __str__( self ):
		return str( self.ref )


class Rule( object ):

	rules = {}
	nextid = 0
	rulemarker = "r"

	@classmethod
	def reset( cls ):
		del cls.rules
		gc.collect()
		cls.rules = {}
		cls.nextid = 0
		cls.rulemarker = "r"
		log.debug( " index reset" )

	@classmethod
	def setrulemarker( cls, marker ):
		cls.rulemarker = marker
		# CAVE: invalidates all Index keys refering to rules; implies Index reset

	def __init__( self ):
		self.guard = Symbol( self, guard=True )
		self.guard.next = self.guard
		self.guard.prev = self.guard
		self.id = Rule.nextid
		Rule.nextid += 1
		Rule.rules[self.id] = self
		self.refs = set()
		log.debug( " Rule.nextid=%s Rule.rules=%s" % (Rule.nextid, Rule.rules) )
		log.info( " new rule %s" % (self) )

	def __del__( self ):
		log.debug( " delete rule %s" % self )
		del Rule.rules[self.id]

	def refcount( self ):
		return len( self.refs )

	def append( self, ref ):
		symbol = Symbol( ref )
		log.debug( " append symbol %s to %s" % (symbol, self) )
		guard = self.guard
		head = guard.prev
		head.nextdisconnect() # disconnect from guard
		symbol.nextconnect( guard )
		head.nextconnect( symbol ) # connect last to avoid operating on dangling digrams
		if isinstance( ref, Rule ):
			ref.refs.add( symbol )
			print "+++++++++++++++ new rule reference for", repr(ref), str(ref), ref.refs
		return symbol

	def each( self ):
		p = self.guard.next
		while not p is self.guard:
			yield p.ref
			p = p.next

	def eachsym( self ):
		p = self.guard.next
		while not p is self.guard:
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

	def replace_digram( self, digram ):
		# ensure rule utility
		assert isinstance( digram, Symbol )
		a,b = digram.digram()
		log.info( " replace digram %s,%s with rule %s" % (repr(a)+str(a), repr(b)+str(b), repr(self)+str(self)) )
		new = digram.replace_digram( Symbol( self ) )
		self.refs.add( new )
		print "+++++++++++++++ new rule reference for", repr(self), str(self), self.refs
		if isinstance( a.ref, Rule ): a.ref.killref( a )
		if isinstance( b.ref, Rule ): b.ref.killref( b )
		log.debug( " rule refs of %s: %s" % (repr(self)+str(self),str(self.refs)) )
		return new

	def delete( self ):
		assert len( self.refs ) == 1
		ref = self.refs.pop()
		log.info( " delete last rule reference at %s for rule %s" % (repr(ref)+str(ref),repr(self)+str(self)) )
		#embed() 
		# restore rule in place
		# leaving the connection between the two symbols in the rule intact
		# will keep the digram in the index which is okay in this special case. 
		#TODO: move functionality to Symbol class?
		prev = ref.prev
		next = ref.next
		tail = self.guard.next
		head = self.guard.prev

		# TODO: debugging hack
		#p = ref
		#while not p.is_guard(): p = p.prev
		#p = p.ref.ref # now is parent rule pointer
		#print "/////////////////////////////////////"
		#print p.dump()
		#print index.dict

		ref.replace_symbol( tail, head )
		del Rule.rules[self.id]

		#print p.dump()
		#print index.dict


	def killref( self, ref ):
		log.debug( " killing reference to %s in rule %s" % (repr(ref)+str(ref),repr(self)+str(self)) )
		#embed()
		try:       #TODO: ##############################################uglyhack####################
			self.refs.remove( ref )
			print "---------------- killed rule reference for", repr(ref), str(ref), self.refs
		except KeyError:
			log.warning( " trying to kill unregistered ref %s" % str(ref) )
		if self.refcount() == 1: self.delete()

	@classmethod
	def makeunique( cls, oldmatch, newmatch ):
		if oldmatch.prev.is_guard() and oldmatch.next.next.is_guard():
			# full rule match, ruse existing rule
			oldrule = oldmatch.prev.ref.ref
			log.debug( " makeunique with full rule %s replacing %s" % (oldrule,repr(newmatch)) )
			oldrule.replace_digram( newmatch )
			return False
		else:
			# create a new rule of the old digram
			log.debug( " create new rule from %s and %s" % (oldmatch, oldmatch.next) )

			# assuming that oldmatch is aready removed from the index
			# else recursion on second append
			newrule = Rule()
			newrule.append( oldmatch.ref ) # .ref ensures that symbol copy is used for rule
			newrule.append( oldmatch.next.ref )

			# replace both instances with new rule reference
			newrule.replace_digram( oldmatch )
			newrule.replace_digram( newmatch )

			# TODO: cleanup/unlink oldmatch and newmatch?
			return newrule

	@classmethod
	def makeunique_disabled( cls, oldmatch, newmatch ):
			pass

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
		return Rule.rulemarker + str( self.id )

def print_state():
	print "::::::::::::::::: Rules ::::::::::::::::::"
	for i in Rule.rules:
		r = Rule.rules[i]
		print " ", repr(r), "    ", str(r)
		for d in r.eachsym():
			print "   ", repr(d), "  ", str(d)
		print "      References:"
		for ref in r.refs:
			print "          ", repr(ref), str(ref)
	print "::::::::::::::::: Index ::::::::::::::::::"
	for key in index.dict:
		s = index.dict[key]
		print " ", repr(s), "  ", key


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
	log.basicConfig( level=log.WARNING )
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

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
		if seenat:
			overlap = seenat.next is symbol
		 	if not overlap:
				Rule.makeunique( seenat, symbol )
				return False
			else:
				return False
		else:
			# actually learn
			key = self.key( symbol )
			log.debug( " index learning %s at %s" % (str(key), symbol.debugstr()) )
			self.dict[key] = symbol
			return True

	def forget( self, symbol ):
		"""removes symbol digram from the dictionary"""
		if symbol.is_guard() or symbol.next.is_guard(): return False
		key = index.key( symbol )
		log.debug( " index forgetting '%s' at %s" % (str(key), symbol.debugstr()) )
		try:
			if self.dict[key] == symbol: del self.dict[key]
			log.debug( " index forgets %s" % key )
		except KeyError:
			raise KeyError( "key '%s' from digram %s not in index" % (str(key), repr(symbol)) )
		return True

	def __str__( self ):
		return ( self.dict )

# Global instance of the Index
index = Index()

class SymbolError( Exception ):
	pass

class Symbol( object ):
	"""A helper class to faciliate pointer arithmetics"""

	def __init__( self, reference ):
		self.ref = reference
		self.prev = self
		self.next = self
		if isinstance( self.ref, Rule ): self.ref.addref( self )
		log.debug( " new symbol %s with reference to %s" % (self.debugstr(), str(reference)) )

	def delete( self ):
		log.debug( " symbol %s is being deleted" % repr(self) )
		if self.is_connected():
			raise SymbolError( "connected %s marked for deletion" % repr(self) )
		if isinstance( self.ref, Rule ): self.ref.killref( self )
		del self.ref
		del self.next
		del self.prev

	def is_connected( self ):
		if self.next is self:
			if self.prev is self:
				return False
			else:
				raise SymbolError( "%s has broken prev/next connection" % repr(self) )
		else:
			if self.prev is not self:
				return True
			else:
				raise SymbolError( "%s has broken next/prev connection" % repr(self) )

	def is_guard( self ):
		return isinstance( self.ref, Symbol )

	def insertnext( self, next ):
		log.debug( " inserting %s right of %s" % (next.debugstr(),self.debugstr()) )
		if next.is_connected():
			raise SymbolError( "%s cannot be connected to still-connected %s" % (repr(self),repr(next)) )
		oldnext = self.next
		oldnext.prev = next
		next.next = oldnext
		self.next = next
		next.prev = self

	def digram( self ):
		if self.next.is_guard():
			raise SymbolError( "digram call to guard node %s" % repr(self) )
		if self.is_guard():
			raise SymbolError( "digram call to guard symbol %s" % repr(self) )
		if not self.is_connected():
			raise SymbolError( "digram call unconnected symbol %s" % repr(self) )
		return self, self.next

	def refdigram( self ):
		tail,head = self.digram()
		return tail.ref, head.ref

	def replace_digram( self, rule ):
		"""replaces this digram with newly-formed symbol referencing rule.
		   returns the newly-formed symbol.
		""" 
		newsymbol = Symbol( rule )
		tail,head = self.digram()
		prev = tail.prev
		next = head.next
		# new connections
		next.prev = newsymbol
		newsymbol.next = next
		newsymbol.prev = prev
		prev.next = newsymbol	
		# disconnect tail and head
		tail.prev = tail
		tail.next = tail
		tail.delete()
		head.prev = head
		head.next = head
		head.delete()
		return newsymbol

	def replace_symbol( self, rule ):
		"""replaces this symbol by content of rule.
		   the rule is left properly emptied-out.
		   returns tail and head of what was replaced.
		   triggers deletion of this symbol.
		"""
		prev = self.prev
		next = self.next
		guard, tail, head = rule.nodes()
		# insert rule symbols)
		next.prev = head
		head.next = next
		tail.prev = prev
		prev.next = tail
		# diconnect rule and self
		guard.prev = guard
		guard.next = guard
		self.prev = self
		self.next = self
		self.delete() # will trigger rule deletion
		return tail, head

	def debugstr( self ):
		return repr(self) + " " + str( self.ref )

	def __str__( self ):
		return str( self.ref )

class RuleError( Exception ):
	pass

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
		self.id = Rule.nextid
		Rule.nextid += 1
		self.refs = set() # must be here before guard creation
		self.guard = Symbol( Symbol( self ) ) # distinctive for guard, creates rule reference
		self.refs.remove( self.guard.ref ) # helps later on
		Rule.rules[self.id] = self
		log.debug( " new rule %s with id %s" % (self.debugstr(),str(self.id)) )

	def delete( self ):
		if not self.is_empty():
			raise RuleError( "cannot delete non-empty rule %s" % repr(self) )
		# dismantle rule
		del Rule.rules[self.id]
		self.guard.ref.ref = None # else delete will trigger rule dereference via killref path
		self.guard.ref.delete()
		self.guard.delete()
		del self.guard
		del self.refs

	def is_empty( self ):
		if not self.guard.is_connected():
			if self.refcount() == 0:
				return True
		return False
		#TODO: fill out error condition
		#raise RuleError( " deleted rule %s is still in index" % repr(self) )

	def nodes( self ):
		"""returns list of this rule's guard, tail and head symbols"""
		guard = self.guard
		tail = guard.next
		head = guard.prev
		return guard, tail, head

	def refcount( self ):
		return len( self.refs )

	def addref( self, symbol ):
		log.debug( " adding rule reference to %s by %s" % (self.debugstr(), symbol.debugstr()) )
		self.refs.add( symbol )

	def killref( self, symbol ):
		log.debug( " killing rule reference to %s by %s" % (self.debugstr(), symbol.debugstr()) )
		try:
			self.refs.remove( symbol )
		except KeyError:
			raise RuleError( "killref for unknown reference to %s by %s" % (repr(self), repr(symbol)) )
		# enforce rule utility
		if self.refcount() == 1:
			self.replace_lastref() # beware of the recursion
		elif self.refcount() == 0:
			self.delete()

	def each( self ):
		symbol = self.guard.next
		while not symbol is self.guard:
			yield symbol.ref
			symbol = symbol.next

	def eachsymbol( self ):
		symbol = self.guard.next
		while not symbol is self.guard:
			yield symbol
			symbol = symbol.next

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

	def append( self, newref ):
		newsymbol = Symbol( newref )
		log.debug( " appending symbol %s to %s" % (newsymbol.debugstr(), self.debugstr()) )
		head = self.guard.prev
		# make new connection
		head.insertnext( newsymbol )
		# learn newly-formed digram
		index.learn( head ) # might be guard
		return newsymbol

	def replace_digram( self, digram ):
		"""replaces digram with reference to this rule.
		   returns the newly-formed symbol.
		   forgets broken and learns new digrams.
		"""
		# ensure rule utility
		log.debug( " replacing digram at %s with rule %s" % (digram.debugstr(), self.debugstr()) )
		# forget broken digrams
		index.forget( digram.prev )
		index.forget( digram.next )
		newsymbol = digram.replace_digram( self )
		#learn new digrams
		index.learn( newsymbol ) # newsymbol.next might be a guard
		index.learn( newsymbol.prev ) # might be a guard
		return newsymbol

	def replace_lastref( self ):
		"""replaces last reference to this rule with the rule's content.
		   leaves empty rule.
	   	   forgets broken and learns new digrams.
		"""
		if len( self.refs ) != 1:
			raise RuleError #TODO: nice message
		lastref = self.refs.copy().pop() # deleted via following symbol deletion trigger
		log.debug( " deleting rule %s with last reference %s" % (self.debugstr(), lastref.debugstr()) )
		# forget broken digrams
		index.forget( lastref.prev ) # lastref.prev might be guard
		index.forget( lastref ) # lastref.next might be guard
		tail, head = lastref.replace_symbol( self )
		# learn new digrams
		index.learn( head ) # head.next might be guard
		index.learn( tail.prev ) # might be guard

	@classmethod
	def makeunique( cls, oldmatch, newmatch ):
		if oldmatch.prev.is_guard() and oldmatch.next.next.is_guard():
			# full rule match, ruse existing rule
			oldrule = oldmatch.prev.ref.ref
			log.debug( " makeunique with full rule %s replacing %s" % (oldrule.debugstr(),newmatch.debugstr()) )
			oldrule.replace_digram( newmatch )
			return False
		else:
			# create a new rule of the old digram
			log.debug( " create new rule from %s and %s" % (oldmatch, oldmatch.next) )
			# forget old match, else recursion on second rule append
			index.forget( oldmatch )
			# create new rule
			newrule = Rule()
			newrule.append( oldmatch.ref ) # .ref ensures that symbol copy is used for rule
			newrule.append( oldmatch.next.ref )
			# replace both instances with new rule
			newrule.replace_digram( oldmatch )
			newrule.replace_digram( newmatch )
			return newrule

	@classmethod
	def makeunique_disabled( cls, oldmatch, newmatch ):
			pass

	def debugstr( self ):
		return repr( self ) + ' ' + str( self )

	def __str__( self ):
		# TODO: beware of str(rule) <-> symbol ambiguity
		# solution: escaping of rule indicator in non-rule keys
		return Rule.rulemarker + str( self.id )

def print_state():
	print "::::::::::::::::: Rules ::::::::::::::::::"
	for i in Rule.rules:
		r = Rule.rules[i]
		print " ", repr(r), "    ", str(r)
		for d in r.eachsymbol():
			print "   ", repr(d), "  ", str(d)
		print "      References:"
		for ref in r.refs:
			if ref.next != None: # that guard node hack...
				print "       ", repr(ref), str(ref)
	print "::::::::::::::::: Index ::::::::::::::::::"
	for key in index.dict:
		s = index.dict[key]
		print " ", repr(s), "  ", key

class Sequitur( object ):

	def __init__( self ):
		index.reset()
		Rule.reset()
		# create the main sequence rule
		self.S = Rule()

	def append( self, symbol ):
		self.S.append( symbol )

	def walk( self ):
		return self.S.walk()

	def spell_rules( self ):
		a = []
		for i in Rule.rules:
			r = Rule.rules[i]
			s = str(r)+": "
			s += ''.join( r.walk() )
			a.append( s )
		return '\n'.join( a )

	def __str__( self ):
		a = []
		for i in Rule.rules:
			r = Rule.rules[i]
			s = str(r)+": "
			b = []
			for d in r.each():
				if isinstance( d, Rule ):
					b.append(str(d))
				else:
					b.append('"'+str(d).replace('"','\\"')+'"')
			s += ' '.join( b )
			a.append( s )
		return '\n'.join( a )

def main():
	log.basicConfig( level=log.WARNING )
	try:
		filename = sys.argv[1]
	except:
		log.fatal( "ERROR: no filename argument given" )
		sys.exit(5)

	with open( filename ) as f:
		data = bytearray( f.read() )

	s = Sequitur()
	for byte in data:
		s.append( chr(byte) )

	print s
	embed()

if __name__ == '__main__':
	main()

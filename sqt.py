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

	def key( self, digram ):
		"""returns string representing digram in the index"""
		a,b = digram.refdigram()
		return str( a ) + self.keyseparator + str( b )

	def reset( self, keyseparator=',' ):
		"""clears index"""
		del self.dict
		gc.collect()
		self.dict = {}
		self.keyseparator = keyseparator
		log.debug( " index reset" )

	def seen( self, digram ):
		"""returns symbol reference if digram is in index, else False"""
		key = self.key( digram )
		try:
			seenat = self.dict[key]
			log.debug( " index has %s at %s" % (key, repr(seenat)) )
			return seenat
		except KeyError: # not seen
			return False

	def learn( self, digram ):
		"""creates digram reference in the dictionary if digram is new.
		   triggers makeunique() if digram was seen before and does not overlap.
		"""
		# If a digram contains a guard, return False
		# Removes detection logic from Symbol class
		if digram.is_guard() or digram.next.is_guard(): return False
		seenat = self.seen( digram )
		if seenat:
			overlap = (seenat.next is digram) or (seenat.prev is digram)
		 	if not overlap:
				Rule.makeunique( seenat, digram )
				return False
			else: # if else branch runs, overlapping digrams are left-preferenced
				# do not re-learn right-hand side
				# error in Sequitur paper's pseudocode 
				raise RuleError( "learning threesome" )
			#	return False
		# actually learn
		key = self.key( digram )
		log.debug( " index learning %s at %s" % (str(key), digram.debugstr()) )
		self.dict[key] = digram
		return True

	def forget( self, digram ):
		"""removes digram from the dictionary"""
		if digram.is_guard() or digram.next.is_guard(): return False
		key = index.key( digram )
		log.debug( " index to forget '%s' at %s" % (str(key), digram.debugstr()) )
		try:
			log.debug( " index forgetting %s" % key )
			if self.dict[key] == digram: del self.dict[key]
		except KeyError:
			raise KeyError( "key '%s' from digram %s not in index" % (str(key), repr(digram)) )
		return True

	def __str__( self ):
		return ( self.dict )

# Global instance of the Index
index = Index()

class SymbolError( Exception ):
	pass

class Symbol( object ):
	"""A helper class to faciliate pointer arithmetics"""

	def __init__( self, reference, ruleref=True ):
		self.ref = reference
		log.debug( " new symbol %s with reference to %s" % (self.debugstr(), str(reference)) )
		self.prev = self
		self.next = self
		if ruleref and isinstance( self.ref, Rule ): self.ref.addref( self )

	def delete( self ):
		"""frees up pointers to garbage collector.
		   triggers killref() if reference is a rule.
		"""
		log.debug( " symbol %s is being deleted" % repr(self) )
		if self.is_connected():
			raise SymbolError( "connected %s marked for deletion" % repr(self) )
		if isinstance( self.ref, Rule ): self.ref.killref( self )
		del self.ref
		del self.next
		del self.prev

	def is_connected( self ):
		"""returns False if symbol is self-connected, else True."""
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

	def is_threesome( self ):
		"""returns True if this symbol and both neighbors reference the same, else False."""
		return self.ref == self.prev.ref and self.ref == self.next.ref

	def is_guard( self ):
		"""returns True if this symbol is a guard, else False."""
		return isinstance( self.ref, Symbol )

	def insertnext( self, next ):
		"""inserts symbol referenced by next right of this symbol."""
		log.debug( " inserting %s right of %s" % (next.debugstr(),self.debugstr()) )
		if next.is_connected():
			raise SymbolError( "%s cannot be connected to still-connected %s" % (repr(self),repr(next)) )
		oldnext = self.next
		oldnext.prev = next
		next.next = oldnext
		self.next = next
		next.prev = self

	def digram( self ):
		"""returns this symbol and its next-door neighbor."""
		if self.next.is_guard():
			raise SymbolError( "digram call to guard node %s" % repr(self) )
		if self.is_guard():
			raise SymbolError( "digram call to guard symbol %s" % repr(self) )
		if not self.is_connected():
			raise SymbolError( "digram call unconnected symbol %s" % repr(self) )
		return self, self.next

	def refdigram( self ):
		"""returns this symbol's reference and that of its next-door neighbor."""
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
		"""returns verbose string representation for debug output"""
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
		"""clears class-wide rule index."""
		del cls.rules
		gc.collect()
		cls.rules = {}
		cls.nextid = 0
		cls.rulemarker = "r"
		log.debug( " index reset" )

	@classmethod
	def setrulemarker( cls, marker ):
		"""defines a new rule marker"""
		cls.rulemarker = marker
		# CAVE: invalidates all Index keys refering to rules; implies Index reset
		#TODO: if rule marker moves to rule ID, rule index is invalidated, too

	def __init__( self ):
		self.id = Rule.nextid
		log.debug( " new rule %s with id %s" % (self.debugstr(),str(self.id)) )
		Rule.nextid += 1
		self.refs = set() # must be here before guard creation
		self.guard = Symbol( Symbol( self, ruleref=False ) ) # distinctive for guard
		Rule.rules[self.id] = self

	def delete( self ):
		"""removes this rule from rule index and frees references for garbage collector."""
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
		"""returns True if guard symbol has no neighbors, else False."""
		if not self.guard.is_connected():
			if self.refcount() == 0:
				return True
		return False

	def nodes( self ):
		"""returns list of this rule's guard, tail and head symbols"""
		guard = self.guard
		tail = guard.next
		head = guard.prev
		return guard, tail, head

	def refcount( self ):
		"""returns number of symbols referencing this rule."""
		return len( self.refs )

	def addref( self, symbol ):
		"""adds symbol to this rule's references set."""
		log.debug( " adding rule reference to %s by %s" % (self.debugstr(), symbol.debugstr()) )
		self.refs.add( symbol )

	def killref( self, symbol ):
		"""deletes symbol from this rule's references set.
		   triggers replace_lastref() if there is only one reference left.
		   triggers this rule's deletion if there are no more references.
		"""
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
		"""iterator yielding the ordered references this rule contains."""
		symbol = self.guard.next
		while not symbol is self.guard:
			yield symbol.ref
			symbol = symbol.next

	def eachsymbol( self ):
		"""iterator yielding the ordered symbols this rule contains."""
		symbol = self.guard.next
		while not symbol is self.guard:
			yield symbol
			symbol = symbol.next

	def dump( self ):
		"""returns ordered list of references this rule makes."""
		return [ref for ref in self.each()]

	def walk( self ):
		"""returns ordered list of references this tule makes
		   and recursively resolves rule references.
		"""
		result = []
		for ref in self.each():
			if isinstance( ref, Rule ):
				result.extend( ref.walk() )
			else:
				result.append( ref )
		return result

	def append( self, newref, learn=True ):
		"""wraps newref into symbol and appends it to this rule's head."""
		newsymbol = Symbol( newref )
		log.debug( " appending symbol %s to %s" % (newsymbol.debugstr(), self.debugstr()) )
		head = self.guard.prev
		# make new connection
		head.insertnext( newsymbol )
		# learn newly-formed digram
		index.learn( head )
		return newsymbol

	def replace_digram( self, digram ):
		"""replaces digram with reference to this rule.
		   returns the newly-formed symbol.
		   forgets broken and learns new digrams.
		"""
		# ensure rule utility
		log.debug( " replacing digram at %s with rule %s" % (digram.debugstr(), self.debugstr()) )
		index.forget( digram.prev )
		index.forget( digram ) # else recursion on second rule append
		index.forget( digram.next.next )
		index.forget( digram.next )
		# overlap corrections
		if digram.next.next.is_threesome(): index.learn( digram.next.next )
		if digram.prev.is_threesome(): index.learn( digram.prev.prev )
		newsymbol = digram.replace_digram( self )
		# learn new
		index.learn( newsymbol )
		index.learn( newsymbol.prev )
		return newsymbol

	def replace_lastref( self ):
		"""replaces last reference to this rule with the rule's content.
		   leaves empty rule.
	   	   forgets broken and learns new digrams.
		"""
		#if len( self.refs ) != 1:
		#	raise RuleError #TODO: nice message
		lastref = self.refs.copy().pop() # deleted via following symbol deletion trigger
		log.debug( " deleting rule %s with last reference %s" % (self.debugstr(), lastref.debugstr()) )
		# forget broken digrams
		index.forget( lastref.prev )
		index.forget( lastref )
		# overlaps
		if lastref.next.is_threesome(): index.learn( lastref.next )
		if lastref.prev.is_threesome(): index.learn( lastref.prev.prev )
		tail, head = lastref.replace_symbol( self )
		# learn new digrams
		index.learn( tail.prev )
		index.learn( head )
		return tail, head

	@classmethod
	def makeunique( cls, oldmatch, newmatch ):
		"""enforces digram uniqueness by replacing newmatch with rule reference.
		   if oldmatch is a rule consisting only of that digram, else form new
		   rule of oldmatch and newmatch and replace both with the new rule reference.
		   returns False on full rule match, else the newly-formed rule.
		"""
		log.debug( " makeunique with oldmatch %s and newmatch %s" % (oldmatch.debugstr(),newmatch.debugstr()) )

		if oldmatch.prev.is_guard() and oldmatch.next.next.is_guard():
			# full rule match, re-use existing rule
			oldrule = oldmatch.prev.ref.ref
			log.debug( " full rule %s replacing %s" % (oldrule.debugstr(),newmatch.debugstr()) )
			newsymbol = oldrule.replace_digram( newmatch )
			return newsymbol

		else:
			# create a new rule of the old digram
			log.debug( " makeunique creating new rule from %s and %s" % (oldmatch, oldmatch.next) )
			newrule = Rule()
			newrule.append( oldmatch.ref, learn=False ) # .ref ensures that symbol copy is used for rule
			newrule.append( oldmatch.next.ref, learn=False )
			oldsymbol = newrule.replace_digram( oldmatch )
			newsymbol = newrule.replace_digram( newmatch )
			index.learn( newrule.guard.next )
			return newrule

	@classmethod
	def makeunique_disabled( cls, oldmatch, newmatch ):
			"""dummy for testing"""
			pass

	def debugstr( self ):
		"""returns verbose string representation for debug output"""
		return repr( self ) + ' ' + str( self )

	def __str__( self ):
		#TODO: beware of str(rule) <-> symbol ambiguity
		# solution: escaping of rule indicator in non-rule keys
		#TODO: move marker to rule ID
		return Rule.rulemarker + str( self.id )

def print_state():
	"""dump Sequitur state in readable form"""
	print "::::::::::::::::: Rules ::::::::::::::::::"
	for i in Rule.rules:
		r = Rule.rules[i]
		print " ", repr(r), "    ", str(r)
		for d in r.eachsymbol():
			print "   ", repr(d), "  ", str(d)
		print "      References:"
		for ref in r.refs:
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
		"""append symbol to main rule S."""
		self.S.append( symbol )

	def walk( self ):
		"""iterate over main rule S and recursively yield
		   the sequence of appended symbols.
		"""
		for x in self.S.walk(): yield x

	def spell_rules( self ):
		"""pretty-print all rules. great for character-based input."""
		a = []
		for i in Rule.rules:
			r = Rule.rules[i]
			s = str(r)+": "
			s += ''.join( r.walk() )
			a.append( s )
		return '\n'.join( a )

	def __str__( self ):
		"""returns string-representation of the rule set."""
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
	log.basicConfig( level=log.DEBUG )
	try:
		filename = sys.argv[1]
	except:
		log.fatal( "no filename argument given" )
		sys.exit(5)

	with open( filename ) as f:
		data = bytearray( f.read() )

	s = Sequitur()
	for byte in data:
		s.append( chr(byte) )

	print s
	#embed()

if __name__ == '__main__':
	main()

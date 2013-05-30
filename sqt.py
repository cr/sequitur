#!/usr/bin/env python

import sys
import gc
import logging as log
from IPython import embed


class SymbolError( Exception ):
	pass

class Symbol( object ):
	"""A helper class to faciliate pointer arithmetics"""

	def __init__( self, reference ):
		self.ref = reference
		log.debug( " new symbol %s with reference to %s" % (self.debugstr(), str(reference)) )
		self.l = self
		self.r = self

	def is_guard( self ): return False
	def is_ruleref( self ): return False

	def delete( self ):
		"""frees up pointers to garbage collector."""
		log.debug( " symbol %s is being deleted" % repr(self) )
		if self.is_connected():
			raise SymbolError( "connected %s cannot be deleted" % repr(self) )
		del self.ref
		del self.r
		del self.l

	def is_connected( self ):
		"""returns False if symbol is self-connected, else True."""
		if self.r is self:
			if self.l is self:
				return False
			else:
				raise SymbolError( "%s has broken left/right connection" % repr(self) )
		else:
			if self.l is not self:
				return True
			else:
				raise SymbolError( "%s has broken right/left connection" % repr(self) )

	def is_threesome( self ):
		"""returns True if this symbol and both neighbors reference the same, else False."""
		return self.ref == self.l.ref and self.ref == self.r.ref

	def insertright( self, right ):
		"""inserts symbol referenced by right right of this symbol."""
		log.debug( " inserting %s right of %s" % (right.debugstr(),self.debugstr()) )
		if right.is_connected():
			raise SymbolError( "%s cannot be connected to still-connected %s" % (repr(self),repr(right)) )
		oldright = self.r
		oldright.l = right
		right.r = oldright
		self.r = right
		right.l = self

	def digram( self ):
		"""returns this symbol and its right neighbor."""
		if not self.is_connected():
			raise SymbolError( "digram call unconnected symbol %s" % repr(self) )
		if self.r.is_guard():
			raise SymbolError( "digram %s has neighbor guard %s" % (repr(self),repr(self.r)) )
		return self, self.r

	def refdigram( self ):
		"""returns this symbol's reference and that of its right neighbor."""
		l,r = self.digram()
		return l.ref, r.ref

	def replace_digram( self, symbol ):
		"""replaces this digram with new symbol referencing rule.
		   implicitly increments rule reference.
		   returns the newly-formed symbol.
		""" 
		tail,head = self.digram()
		left = tail.l
		right = head.r
		# new connections
		right.l = symbol
		symbol.r = right
		symbol.l = left
		left.r = symbol	
		# disconnect tail and head
		tail.l = tail
		tail.r = tail
		tail.delete()
		head.l = head
		head.r = head
		head.delete()
		return symbol

	def debugstr( self ):
		"""returns verbose string representation for debug output"""
		return repr(self) + " " + str( self.ref )

	def __str__( self ):
		return str( self.ref )

class Guard( Symbol ):
	def __init__( self, rulereference ):
		if not isinstance( rulereference, Rule ):
			raise TypeError( "argument must be rule reference" )
		super( Guard, self ).__init__( rulereference )
	def is_guard( self ): return True
	def is_ruleref( self ): return False
	def replace_digram( self, rule ): raise NotImplementedError
	def digram( self ): raise NotImplementedError
	def refdigram( self ): raise NotImplementedError
	def is_threesome( self ): return False

class Ruleref( Symbol ):
	def __init__( self, rulereference, ruleref=True ):
		if not isinstance( rulereference, Rule ):
			raise TypeError( "argument must be rule reference" )
		super( Ruleref, self ).__init__( rulereference )
		if ruleref: self.ref.addref( self )

	def is_guard( self ): return False
	def is_ruleref( self ): return True

	def delete( self, killref=True ):
		"""frees up pointers to garbage collector.
		   triggers killref() for referenced rule.
		"""
		if killref: self.ref.killref( self )
		super( Ruleref, self ).delete()

	def replace( self ):
		"""replaces this symbol by content of rule it refers.
		   the rule is left properly emptied-out.
		   triggers deletion of this ruleref symbol.
		   returns tail and head of what was replaced.
		"""
		left = self.l
		right = self.r
		guard, tail, head = self.ref.nodes()
		# insert rule symbols)
		right.l = head
		head.r = right
		tail.l = left
		left.r = tail
		# diconnect rule and self
		guard.l = guard
		guard.r = guard
		self.l = self
		self.r = self
		self.delete() # will trigger rule deletion
		return tail, head

class Index( object ):
	"""Class for speedy lookups of digram occurrence"""

	# callback for makeunique
	makeunique = ( lambda *args, **kw: None ) # ultimately Rule.makeunique

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

	def learn( self, digram, makeunique=makeunique ):
		"""creates digram reference in the dictionary if digram is new.
		   triggers makeunique() if digram was seen before and does not overlap.
		"""
		# If a digram contains a guard, return False
		# Removes detection logic from Symbol class
		if digram.is_guard() or digram.r.is_guard(): return False
		seenat = self.seen( digram )
		if seenat:
			overlap = (seenat.r is digram) or (seenat.l is digram)
		 	if not overlap:
				if makeunique: makeunique( seenat, digram )
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
		if digram.is_guard() or digram.r.is_guard(): return False
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

class RuleError( Exception ):
	pass

class Rule( object ):

	rules = {}
	rightid = 0
	rulemarker = "r"
	forget = ( lambda *args, **kw: None )
	learn = ( lambda *args, **kw: None )

	@classmethod
	def reset( cls, rulemarker='r' ):
		"""clears class-wide rule index."""
		del cls.rules
		gc.collect()
		cls.rules = {}
		cls.rid = 0
		cls.rulemarker = rulemarker
		log.debug( " Rule reset" )
		index.reset()

	def __init__( self ):
		self.id = str(Rule.rulemarker) + str(Rule.rid)
		log.debug( " new rule %s with id %s" % (self.debugstr(),str(self.id)) )
		Rule.rid += 1
		self.refs = set() # must be here before guard creation
		self.guard = Guard( self )
		Rule.rules[self.id] = self

	def delete( self ):
		"""removes this rule from rule index and frees references for garbage collector."""
		if not self.is_empty():
			raise RuleError( "cannot delete non-empty rule %s" % repr(self) )
		# dismantle rule
		del Rule.rules[self.id]
		self.guard.delete()
		del self.guard
		del self.refs

	def is_empty( self ):
		"""returns True if guard symbol has no neighbors, else False."""
		return not self.guard.is_connected()

	def nodes( self ):
		"""returns list of this rule's guard, tail and head symbols"""
		guard = self.guard
		tail = guard.r
		head = guard.l
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
		   triggers dissolve() if there is only one reference left.
		   triggers this rule's deletion if there are no more references.
		"""
		log.debug( " killing rule reference to %s by %s" % (self.debugstr(), symbol.debugstr()) )
		try:
			self.refs.remove( symbol )
		except KeyError:
			raise RuleError( "killref for unknown reference to %s by %s" % (repr(self), repr(symbol)) )
		# enforce rule utility
		if self.refcount() == 1:
			self.dissolve() # beware of the recursion
		elif self.refcount() == 0:
			self.delete()

	def each( self ):
		"""iterator yielding the ordered references this rule contains."""
		symbol = self.guard.r
		while not symbol.is_guard():
			yield symbol.ref
			symbol = symbol.r

	def eachsymbol( self ):
		"""iterator yielding the ordered symbols this rule contains."""
		symbol = self.guard.r
		while not symbol.is_guard():
			yield symbol
			symbol = symbol.r

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

	def append( self, newref, learn=learn ):
		"""wraps newref into symbol and appends it to this rule's head."""
		if isinstance( newref, Rule ):
			newsymbol = Ruleref( newref )
		else:
			newsymbol = Symbol( newref )
		log.debug( " appending symbol %s to %s" % (newsymbol.debugstr(), self.debugstr()) )
		head = self.guard.l
		# make new connection
		head.insertright( newsymbol )
		# learn newly-formed digram
		if learn: learn( head )
		return newsymbol

	def replace_digram( self, digram, learn=learn, forget=forget ):
		"""replaces digram with reference to this rule.
		   returns the newly-formed symbol.
		   forgets broken and learns new digrams.
		"""
		# ensure rule utility
		log.debug( " replacing digram at %s with rule %s" % (digram.debugstr(), self.debugstr()) )
		if forget:
			forget( digram.l )
			forget( digram ) # else recursion on second rule append
			forget( digram.r.r )
			forget( digram.r )
		# overlap corrections
		if digram.r.r.is_threesome() and learn: learn( digram.r.r )
		if digram.l.is_threesome()   and learn: learn( digram.l.l )
		newsymbol = digram.replace_digram( Ruleref( self ) )
		# learn new
		if learn:
			learn( newsymbol )
			learn( newsymbol.l )
		return newsymbol

	def dissolve( self, learn=learn, forget=forget ):
		"""replaces last reference to this rule with the rule's content.
		   leaves empty rule.
	   	   forgets broken and learns new digrams.
		"""
		#if len( self.refs ) != 1:
		#	raise RuleError #TODO: nice message
		lastref = self.refs.copy().pop() # deleted via following symbol deletion trigger
		log.debug( " deleting rule %s with last reference %s" % (self.debugstr(), lastref.debugstr()) )
		# forget broken digrams
		if forget:
			forget( lastref.l )
			forget( lastref )
		# overlaps
		if lastref.r.is_threesome() and learn: learn( lastref.r )
		if lastref.l.is_threesome() and learn: learn( lastref.l.l )
		tail, head = lastref.replace()
		# learn new digrams
		if learn:
			learn( tail.l )
			learn( head )
		return tail, head

	@classmethod
	def makeunique( cls, oldmatch, newmatch ):
		"""enforces digram uniqueness by replacing newmatch with rule reference.
		   if oldmatch is a rule consisting only of that digram, else form new
		   rule of oldmatch and newmatch and replace both with the new rule reference.
		   returns False on full rule match, else the newly-formed rule.
		"""
		log.debug( " makeunique with oldmatch %s and newmatch %s" % (oldmatch.debugstr(),newmatch.debugstr()) )

		if oldmatch.l.is_guard() and oldmatch.r.r.is_guard():
			# full rule match, re-use existing rule
			oldrule = oldmatch.l.ref.ref
			log.debug( " full rule %s replacing %s" % (oldrule.debugstr(),newmatch.debugstr()) )
			newsymbol = oldrule.replace_digram( newmatch )
			return newsymbol

		else:
			# create a new rule of the old digram
			log.debug( " makeunique creating new rule from %s and %s" % (oldmatch, oldmatch.r) )
			newrule = Rule()
			newrule.append( oldmatch.ref, learn=False ) # .ref ensures that symbol copy is used for rule
			newrule.append( oldmatch.r.ref, learn=False )
			oldsymbol = newrule.replace_digram( oldmatch )
			newsymbol = newrule.replace_digram( newmatch )
			index.learn( newrule.guard.r )
			return newrule

	# make index use this callback
	Index.makeunique = makeunique 


	def debugstr( self ):
		"""returns verbose string representation for debug output"""
		return repr( self ) + ' ' + str( self )

	def __str__( self ):
		#TODO: beware of str(rule) <-> symbol ambiguity
		# solution: escaping of rule indicator in non-rule keys
		#TODO: move marker to rule ID
		return self.id

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
		Rule.reset()
		index.reset()
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

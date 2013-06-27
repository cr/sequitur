type SymLink = Option<@mut Symbol>;
type RefLink = Option<@mut Symref>;

enum Symref {
	Guard( @mut Rule ),
	Nonterminal( @mut Rule ),
	Terminal( @str )
}

impl Symref {
	fn as_str( sr: @mut Symref ) -> ~str { sr.to_str() }
	fn to_str( &self ) -> ~str {
		match *self {
			Terminal( sym ) => sym.to_str(),
			Nonterminal( rule ) => rule.to_str(),
			Guard( _rule ) => fail!( ~"to_str() called on Guard")
		}
	}
}

struct Symbol { left: SymLink, right: SymLink, ptr: RefLink }

impl Symbol {
	fn insert_after( @mut self, newright: @mut Symbol ) {
		// turn self <-> oldright
		// into self <-> newright <-> oldright
		//let oldright = match self.right { Some( x ) => x, None => fail!() };
		let oldright = self.right.get();
		oldright.left = Some( newright );
		newright.right = Some( oldright );
		newright.left = Some( self );
		self.right = Some( newright );
	}
	fn get_left( &self ) -> @mut Symbol { self.left.get() }
	fn get_right( &self ) -> @mut Symbol { self.right.get() }
	fn get_ref( &self ) -> @mut Symref { self.ptr.get() }
	fn to_str( &self ) -> ~str { self.get_ref().to_str() }
	fn print( &self ) { print( self.to_str() ); }
	fn println( &self ) { println( self.to_str() ); }
	fn replace_digram( @mut self, rule: @mut Rule ) -> @mut Symbol { 
		let newsymbol = @mut Symbol { left: None, right: None, ptr: None };
		newsymbol.ptr = Some( @mut Nonterminal( rule ) );
		let left = self.get_left();
		let right = self.get_right();
		let rightright = right.get_right();
		rightright.left = Some( newsymbol );
		newsymbol.right = Some( rightright );
		newsymbol.left = Some( left );
		left.right = Some( newsymbol );
		self.left = None;
		self.right = None;
		self.ptr = None;
		right.left = None;
		right.right = None;
		right.ptr = None;
		return newsymbol;
	}
	fn dissolve( @mut self ) {
		let rule = match self.get_ref() {
			@Nonterminal( rule ) => rule,
			_ => fail!()
		};
		let left = self.get_left();
		let right = self.get_right();
		let tail = rule.get_tail();
		let head = rule.get_head();
		right.left = Some( head );
		head.right = Some( right );
		tail.left = Some( left );
		left.right = Some( tail );
		self.left = None;
		self.right = None;
		self.ptr = None;
		rule.del_ref( &self );
	}
}

impl Eq for Symbol {
	fn eq( &self, v2: &Symbol ) -> bool { core::ptr::ref_eq( self, v2 ) }
	fn ne( &self, v2: &Symbol ) -> bool { !core::ptr::ref_eq( self, v2 ) }
}

struct Rule { id: uint, guard: @mut Symbol, refs: ~[@mut Symbol] }

impl Rule {
	fn new( id: uint ) -> @mut Rule {
		let guard = @mut Symbol { left: None, right: None, ptr: None };
		guard.left = Some( guard );
		guard.right = Some( guard );
		let self = @mut Rule { id: id, guard: guard, refs: ~[] };
		guard.ptr = Some( @mut Guard( self ) );
		return self;
	}
	fn get_guard( &self ) -> @mut Symbol { self.guard }
	fn get_tail( &self ) -> @mut Symbol { self.guard.right.get() }
	fn get_head( &self ) -> @mut Symbol { self.guard.left.get() }
	fn get_id( &self ) -> uint { self.id }
	fn append( &self, s: @str ) {
		let symbol = @mut Symbol { left: None, right: None, ptr: None };
		symbol.ptr = Some( @mut Terminal( s ) );
		let head = self.get_head();
		head.insert_after( symbol );
	}
	fn apply( @mut self, symbol: @mut Symbol ) -> @mut Symbol {
		let new = symbol.replace_digram( self );
		self.add_ref( new );
		return new;
	}
	fn delete( @mut self ) {
		let lastref = self.refs.pop();
		lastref.dissolve();
		//assert!( self.refs.len() == 1 );
		self.guard.left = None;
		self.guard.right = None;
		self.guard.ptr = None;
		//remove from rule index
	}
	fn add_ref( @mut self, s: @mut Symbol ) {
		self.refs.push( s );
	}
	fn del_ref( &mut self, s: &@mut Symbol ) {
		println( fmt!( "delref len %d", self.refs.len() as int ) );
		match self.refs.position_elem( s ) {
			Some( position ) => { self.refs.swap_remove( position ); }
			None =>	{ fail!( ~"del_ref() called for non-referencing symbol" ) }
		}
	}
	fn refcount( &self ) -> uint { self.refs.len() }
	fn to_str( &self ) -> ~str { ~"r" + uint::to_str( self.get_id() ) }
	fn to_rule_str( &self ) -> ~str {
		let mut res = self.to_str() + ~":";
		let mut esc = ~"";
		for vec::each( self.to_vec() ) |s| {
			esc = s.to_str();
			esc = core::str::escape_default( esc );
			esc = core::str::replace( esc, ~" ", ~"\\ " );
			res += ~" " + esc;
		}
		res
	}
	fn to_vec( &self ) -> ~[@mut Symref] {
		let mut res = ~[];
		let guard = self.get_guard();
		let mut ptr = guard.get_right();
		loop {
			let p = ptr.ptr.get();
			match p {
				@Guard( _rule ) => { return res; }
				//_ => { vec::push( &mut res, p ); }
				_ => { res.push( p ); }
			}
			ptr = ptr.get_right();
		}
	}
	fn to_str_vec( &self ) -> ~[~str] {
		let mut res = ~[];
		let guard = self.get_guard();
		let mut ptr = guard.get_right();
		loop {
			let p = ptr.ptr.get();
			match p {
				@Guard( _rule ) => { return res; }
				_ => { vec::push( &mut res, p.to_str() ); }
			}
			ptr = ptr.get_right();
		}
	}
	fn print( &self ) { print( self.to_rule_str() ); }
	fn println( &self ) { println( self.to_rule_str() ); }
}

#[test]
fn test_rule_append() {
	let r = Rule::new( 23 );
	let guard = r.get_guard();
	assert!( core::managed::mut_ptr_eq( r.get_tail(), guard ) );
	assert!( core::managed::mut_ptr_eq( r.get_head(), guard ) );
	r.append( @"1" );
	r.append( @"2" );
	r.append( @"3" );
	assert_eq!( r.to_rule_str(), ~"r23: 1 2 3" );
}

#[test]
fn test_rule_apply() {
	let r = @mut Rule::new( 0 );
	r.append( @"1" );
	r.append( @"2" );
	r.append( @"1" );
	r.append( @"2" );
	let s = @mut Rule::new( 1 );
	s.append( @"1" );
	s.append( @"2" );
	let a = r.get_tail();
	let b = r.get_head().get_left();
	assert_eq!( r.to_rule_str(), ~"r0: 1 2 1 2" );
	assert_eq!( s.to_rule_str(), ~"r1: 1 2" );
	let newa = s.apply( a );
	assert!( core::managed::mut_ptr_eq( r.get_tail(), newa ) );
	assert_eq!( r.to_rule_str(), ~"r0: r1 1 2" );
	assert_eq!( s.to_rule_str(), ~"r1: 1 2" );	
	let newb = s.apply( b );
	assert!( core::managed::mut_ptr_eq( r.get_head(), newb ) );
	assert_eq!( r.to_rule_str(), ~"r0: r1 r1" );
	assert_eq!( s.to_rule_str(), ~"r1: 1 2" );
}

#[test]
fn test_rule_ref() {
	let r = @mut Rule::new( 0 );
	r.append( @"1" );
	r.append( @"2" );
	r.append( @"1" );
	r.append( @"2" );
	let s = @mut Rule::new( 1 );
	s.append( @"1" );
	s.append( @"2" );
	let a = r.get_tail();
	let b = r.get_head().get_left();
	println( fmt!( "%d", s.refcount() as int ) );
	let newa = s.apply( a );
	println( fmt!( "%d", s.refcount() as int ) );
	let _newb = s.apply( b );
	println( fmt!( "%d", s.refcount() as int ) );
	newa.dissolve();
	println( fmt!( "%d", s.refcount() as int ) );
	s.delete();
	println( fmt!( "%d", s.refcount() as int ) );
}

fn main() {
//	let args = os::args();
//	if args.len() < 1 { fail!( ~"Usage: sqt <file>" ); }
	let r = Rule::new( 0 );
	r.append( @"hello" );
	r.append( @"sequitur" );
	r.append( @"ä \\foobar" );
	r.append( @"\n" );
	println( r.to_rule_str() );
}

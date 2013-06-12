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
	}
}

//impl Eq for Symbol {
//	fn eq( &self, other: &@mut Symbol ) -> bool { core::managed::mut_ptr_eq( self, other ) }
//	fn ne( &self, other: &@mut Symbol ) -> bool { ! core::managed::mut_ptr_eq( self, other ) }
//}

struct Rule { id: uint, guard: @mut Symbol, refs: ~[@Symbol] }

impl Rule {
	fn new( id: uint ) -> @mut Rule {
		let guard = @mut Symbol { left: None, right: None, ptr: None };
		guard.left = Some( guard );
		guard.right = Some( guard );
		let self = @mut Rule { id: id, guard: guard, refs: ~[] };
		guard.ptr = Some( @mut Guard( self ) );
		return self
	}
	fn get_guard( &self ) -> @mut Symbol { self.guard }
	fn get_tail( &self ) -> @mut Symbol { self.guard.right.get() }
	fn get_head( &self ) -> @mut Symbol { self.guard.left.get() }
	fn get_id( &self ) -> uint { self.id }
	fn append( &self, s: @str ) {
		let symbol = @mut Symbol { left: None, right: None, ptr: Some( @mut Terminal( s ) ) };
		let head = self.get_head();
		head.insert_after( symbol );
	}
	fn to_str( &self ) -> ~str { ~"r" + uint::to_str( self.get_id() ) }
	fn to_rule_str( &self ) -> ~str {
		let mut res = self.to_str() + ~":";
		for vec::each( self.to_vec() ) |s| { res += ~" " + s.to_str(); }
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
				_ => { vec::push( &mut res, p ); }
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

fn main() {
//	let args = os::args();
//	if args.len() < 1 { fail!( ~"Usage: sqt <file>" ); }
	let r = Rule::new( 0 );
	r.append( @"1" );
	r.append( @"2" );
	r.append( @"3" );
	println( r.to_rule_str() );
}
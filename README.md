# Sequitur

An attempt at Sequitur in Python. After the third rewrite, I am rather confident that it works now. I am even beginning to like the code.

You might want to try implementing it yourself in your favorite programming language. It is at the same time absolutely beautifully mind-blowing and stupefyingly humbling. It will take your relation with that language to a whole new level. Bonus points if that language is functional. In that case: also good luck!

## Usage

Currently it likes text files as input. The main loop feeds the main rule from the file character by character.

```
$ ./sqt.py sqt.py
```

It drops you in an ipython embed() session with the finished Sequitur object in s. Try:

```
print s.spell_rules()
```

## References

* [C. G. Nevill-Manning, I. H. Witten, Identifying Hierarchical Structure in Sequences: A linear-time algorithm](http://arxiv.org/abs/cs/9709102)

PyTat helps you implement code-rewriters.

┌────────────┐           ┌─────┐              ┌───────────────┐
│ input file ├──────────→│ ast ├─────────────→│ custom script │
└────────────┘ parsed by └─────┘ modified by  ├───────────────┤
                                              │     PyTat     │
                                              └───────┬─┬─────┘
         ┌─────────────┐        ┌────────────┐        │ │
         │ output file │←───────┤   astor /  │←───────┘ │
         └─────────────┘ writes │ astunparse │   feeds  │
                ↑       +       └────────────┘          │
                │  writes  ┌───────────┐                │
                └──────────┤ linecache ├────────────────┘
                           └───────────┘     uses


The standard library `ast` module parses Python source into an Abstract Syntax
Tree: the module is divided into statements, where each statement can be
sub-divided into expressions, which can themselves be divided into
sub-expressions, etc.
Then, the most convenient way of navigating the Abstract Syntax Tree is
recursively by subclassing `ast.NodeVisitor`. The `ast.NodeVisitor` class does
nothing but calling callbacks for each AST node. It has (dummy) methods for each
type of AST node, so it's possible to override only a few methods if we're only
interested in the details of some node types (for example, function calls).
To go further, the `ast` module has a `NodeTransformer` class for replacing some
AST nodes by other AST nodes (or adding more nodes, or just removing them).
This is the base of code-rewriting with PyTat.

PyTat script should most likely implement a `NodeTransformer` subclass,
performing the desired modifications. What PyTat brings is that it writes back
the new module.
It writes the new AST nodes into Python source thanks to `astor` dependency (or
any equivalent library), and the untouched AST nodes are written by copying the
original Python source.
The untouched AST nodes could be written into Python with `astor` too, but it
would have a significant drawback. Being about syntax only, an AST doesn't keep
comments, indentation and whitespace, quote style, etc. because this matters for
the lexer level, not the syntax level. So using only `astor`, all this
information would be lost.
So, PyTat combines AST-to-source generation for new content with source extracts
for unmodified parts.

In order to write a PyTat script, it's important to know what are all the AST
nodes that can be encountered. The base `ast` doc is useful but the "Green tree
snakes" is also useful.

https://docs.python.org/3/library/ast.html
https://greentreesnakes.readthedocs.io/en/latest/nodes.html

Another consequence of working at the syntax level is that it's not possible to
determine if an identifier used in an expression refers to a global class, a
local variable, a free variable, is not defined at all, etc.
Names scopes and lookup are at the semantic level, not the syntax level.


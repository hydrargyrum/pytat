Description
-----------

PyTat is a Python 3 library for performing refactoring on Python source code.

Refactoring is done with a combination of AST transforming and original source
extraction (in order to keep comments which are usually lost by AST parsing) for
non-modified parts.

Usage
-----

PyTat is a library. It's typically used by writing a class transforming AST
nodes as desired (see examples dir), and running it on a Python source file.

Dependencies
------------

PyTat uses `astor <https://pypi.org/project/astor/>`_ for converting AST nodes
back to Python source code.

License
-------

PyTat is licensed under the WTFPLv2, see COPYING.WTFPL file for details.

#!/usr/bin/env python3

import ast
import os
import sys

import pytat.lib

# this example will modify a python source file by prepending an extra argument
# to 'print' function calls

class PrintTransformer(pytat.lib.ReplacerVisitor):
    pattern = pytat.lib.ast_expr_from_module(ast.parse('print(_1)'))

    def visit_Call(self, node):
        # process call expressions

        match = pytat.lib.match_ast(self.pattern, node)
        # try to match current call with the pattern
        if match is None:
            # match is None, meaning the call did not match
            # it was probably a call to another function than 'print'
            return node

        # match isn't None, it's a dict capturing placeholder parts of the
        # pattern:
        # the '_1' key will contain the AST node of the argument of
        # the 'print' call

        # create a new 'Call' node
        new_call = ast.Call()

        # let's call the 'print' function
        new_call.func = ast.Name()
        new_call.func.id = 'print'

        # prepend an argument before the existing argument
        new_call.args = [
            ast.Str('output:'),
            match['_1'],
        ]

        new_call.keywords = []

        # done, we replace a Call to print with another Call with one more arg!
        return new_call

    # all other expressions and statement will be untouched


os.chdir(os.path.dirname(sys.argv[0]))
pytat.lib.visit_file('sample1.py', PrintTransformer)

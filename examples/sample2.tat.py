#!/usr/bin/env python3

import ast
import os
import sys

import pytat.lib


def str_to_exp(s):
    return ast.parse(s, mode='eval').body


class PrintTransformer(pytat.lib.TableVisitor):
    replacement_table = {
        # matches print calls with a variable number of arguments
        # and capture arguments in "__1", but no keyword args

        # replace those calls with other calls to print, with args unchanged
        # but add "file=sys.stdout"
        str_to_exp('print(__1)'): str_to_exp('print(__1, file=sys.stdout)'),
    }


os.chdir(os.path.dirname(sys.argv[0]))
pytat.lib.visit_file('sample2.py', PrintTransformer)

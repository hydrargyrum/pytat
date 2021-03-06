#!/usr/bin/env python3

import ast
import os
import sys

import pytat.lib


def str_to_exp(s):
    return ast.parse(s, mode='eval').body


class PrintTransformer(pytat.lib.TableVisitor):
    replacement_table = {
        str_to_exp('print(__1)'): str_to_exp('[__1]'),
    }


os.chdir(os.path.dirname(sys.argv[0]))
pytat.lib.visit_file('exc.py', PrintTransformer)

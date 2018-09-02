# license: WTFPLv2 [http://wtfpl.net]

import ast
import bisect
import linecache
import os
import re
import sys
import tempfile



class State:
    Normal = 0
    Replace = 1


class StatementIndex(ast.NodeVisitor):
    def __init__(self):
        super(StatementIndex, self).__init__()
        self.stmt_lines = set()

    @staticmethod
    def _get_last_lineno(node):
        return getattr(node, 'last_lineno', getattr(node, 'lineno', -1))

    def generic_visit(self, node):
        if not hasattr(node, 'lineno'):
            return

        node.last_lineno = node.lineno

        for f, value in ast.iter_fields(node):
            if isinstance(value, list):
                for sub in value:
                    if isinstance(sub, ast.AST):
                        self.visit(sub)
                        node.last_lineno = max(node.last_lineno, self._get_last_lineno(sub))
            elif isinstance(value, ast.AST):
                self.visit(value)
                node.last_lineno = max(node.last_lineno, self._get_last_lineno(value))

        if isinstance(node, ast.stmt):
            self.stmt_lines.add(node.lineno)

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)


class ReplacerVisitor(ast.NodeTransformer):
    def __init__(self, fn, stmt_lines):
        super(ReplacerVisitor, self).__init__()
        self.fn = fn
        self.first_line = 1
        self.last_line = 1
        self.state = State.Normal
        self.separators = False
        self.stmt_lines = stmt_lines
        self.out = sys.stdout

    def visit(self, node):
        if isinstance(node, ast.stmt):
            return self._visit_stmt(node)

        ret = super(ReplacerVisitor, self).visit(node)
        if ret is not node:
            ast.copy_location(ret, node)
            self.state = State.Replace
        return ret

    def _visit_stmt(self, node):
        if self.state == State.Normal:
            self.last_line = node.lineno
        else:
            assert 0

        ret = self.generic_visit(node)

        if self.state == State.Replace:
            self.last_line = node.lineno
            self.dump_current()

            node_end = self._stmt_end(node)

            if self.separators:
                print('#=# generated code from line', node.lineno, file=self.out)

            src = ast_to_source(ret)
            for line in src.split('\n'):
                print(node.col_offset * ' ', line, sep='', file=self.out)

            if self.separators:
                print('#=# end generated code to line', node_end, file=self.out)

            self.state = State.Normal
            self.first_line = self.last_line = node_end + 1

        return ret

    def dump_current(self):
        if self.separators:
            print('#=# dump from line', self.first_line, file=self.out)

        for i in range(self.first_line, self.last_line):
            print(linecache.getline(self.fn, i), end='', file=self.out)

        if self.separators:
            print('#=# to line', self.last_line - 1, file=self.out)

    def dump_to_end(self):
        if self.separators:
            print('#=# dump after line', self.first_line, file=self.out)

        i = self.first_line
        while True:
            line = linecache.getline(self.fn, i)
            if not line:
                break
            print(line, end='', file=self.out)
            i += 1

        if self.separators:
            print('#=# to the end', file=self.out)

    blank_comments = re.compile(r'|#.*')

    def _stmt_end(self, node):
        index = bisect.bisect_right(self.stmt_lines, node.last_lineno)
        try:
            next_stmt_lineno = self.stmt_lines[index]
        except IndexError:
            return node.last_lineno # TODO should be file end

        i = next_stmt_lineno - 1
        for i in range(next_stmt_lineno - 1, node.last_lineno - 1, -1):
            line = linecache.getline(self.fn, i)
            if not self.blank_comments.fullmatch(line.strip()):
                break
        return i

def match_ast(expected, test):
    """
    Match 2 AST nodes together. If `expected` contains placeholders, they will
    `test` nodes and will be returned in a dict.
    Returns None if nodes don't match. Else return a dict matching placeholders.
    """
    if isinstance(expected, ast.Name) and re.fullmatch(r'_\d+', expected.id):
        return {expected.id: test}

    if type(expected) != type(test):
        return

    if isinstance(expected, ast.Attribute) and re.fullmatch(r'_\d+', expected.attr):
        ret = {expected.attr: test.attr}

        sub = match_ast(expected.value, test.value)
        if sub is None:
            return

        ret.update(sub)
        return ret

    ret = {}
    for (fe, ve), (ft, vt) in zip(ast.iter_fields(expected), ast.iter_fields(test)):
        assert fe == ft

        if isinstance(ve, list):
            if ve and isinstance(ve[0], ast.Name) and re.fullmatch(r'__\d+', ve[0].id):
                assert len(ve) == 1
                ret.update({ve[0].id: vt})
                continue

            if len(ve) != len(vt):
                return
            for vve, vvt in zip(ve, vt):
                sub = match_ast(vve, vvt)
                if sub is None:
                    return

                ret.update(sub)
        elif isinstance(ve, ast.AST):
            sub = match_ast(ve, vt)
            if sub is None:
                return
            ret.update(sub)

        elif ve != vt:
            return

    return ret


def ast_expr_from_module(node):
    """
    Get the `ast.Expr` node out of a `ast.Module` node.
    Can be useful when calling `ast.parse` in `'exec'` mode.
    """
    assert isinstance(node, ast.Module)
    assert len(node.body) == 1
    assert isinstance(node.body[0], ast.Expr)

    return node.body[0].value


def ast_to_source_astor(node):
    import astor

    return astor.to_source(node).strip()


def ast_to_source_unparse(node):
    import astunparse

    return astunparse.unparse(node).strip()


AST_TO_SOURCE_CALLBACKS = (ast_to_source_unparse, ast_to_source_astor)


def ast_to_source(node):
    for cb in AST_TO_SOURCE_CALLBACKS:
        try:
            return cb(node)
        except ImportError:
            pass
    raise ImportError('astunparse or astor should be installed')


def visit_file(filename, cls, inplace=False):
    """
    Read and visit a file using `cls` visitor.

    `cls` must be a `ReplacerVisitor` subclass.
    """
    with open(filename) as fd:
        node = ast.parse(fd.read(), filename)

    liner = StatementIndex()
    liner.visit(node)
    stmt_lines = tuple(sorted(liner.stmt_lines))

    visitor = cls(filename, stmt_lines)
    if inplace:
        visitor.out = tempfile.NamedTemporaryFile(mode='w+t', dir=os.path.dirname(filename))

    visitor.visit(node)
    visitor.dump_to_end()

    if inplace:
        os.link(visitor.out.name, filename)

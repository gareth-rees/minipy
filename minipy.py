#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ast import *
from imp import find_module, load_module
from math import isinf
import re
from string import ascii_lowercase, ascii_uppercase
from sys import stderr, stdout

__author__ = __maintainer__ = 'Gareth Rees'
__email__ = 'gdr@garethrees.org'
__license__ = "GNU General Public License (GPL) Version 3"
__status__ = 'Development'
__version_info__ = (0, 2)
__version__ = '{0}.{1}'.format(*__version_info__)
__all__ = 'serialize_ast reserved_names_in_ast rename_ast detect_encoding'.split()

class Assoc:
    Non = 0
    Left = 1
    Right = 2

class Prec:
    Generator = 0
    Paren = 1
    Tuple = 2
    Lambda = 3
    Or = 4
    Attribute = 17
    Max = 18

class SavePrecedence:
    """
    Context manager class that saves and restores the precedence and
    associativity for a SerializeVisitor instance, and emits a pair of
    parentheses if necessary to preserve the meaning.
    """

    def __init__(self, visitor, prec=Prec.Max, assoc=Assoc.Non, force=False):
        self.v = visitor
        self.new_prec = prec
        self.paren = (force
                      or prec < self.v.prec
                      or prec == self.v.prec
                      and (self.v.assoc == Assoc.Non
                           or self.v.assoc != assoc))

    def __enter__(self):
        self.saved_prec = self.v.prec
        self.saved_assoc = self.v.assoc
        self.saved_operator = self.v.operator
        if self.paren:
            self.v.emit('(')
            self.v.prec = Prec.Paren
            self.v.assoc = Assoc.Non

    def __exit__(self, *e):
        if self.paren:
            self.v.emit(')')
        self.v.prec = self.saved_prec
        self.v.assoc = self.saved_assoc
        self.v.operator = self.saved_operator

class SerializeVisitor(NodeVisitor):
    def __init__(self, docstrings=False, encoding='latin1', indent=1,
                 joinlines=True, selftest=True, **kwargs):
        self.docstrings = docstrings
        self.encoding = encoding
        self.indent = indent
        self.joinlines = joinlines
        self.selftest = selftest
        self.unicode_literals = False

    def selftest_failure(self, result, original, minified):
        import difflib
        return ("RESULT\n{3}\n{0}\n\n"
                "ORIGINAL\n{3}\n{1}\n\n"
                "MINIFIED\n{3}\n{2}\n"
                .format(result, original, minified, '-' * 72))

    def serialize(self, tree):
        self.lastchar = '\n'
        self.lastemit = '\n'
        self.lastnum = False
        self.depth = -1
        self.prec = Prec.Paren
        self.assoc = Assoc.Non
        self.operator = None
        self.result = []
        self.visit(tree)
        result = ''.join(self.result)
        if not self.docstrings and self.selftest:
            original = dump(tree)
            minified = dump(parse(result.decode(self.encoding)))
            if original != minified:
                raise AssertionError, self.selftest_failure(result, original, minified)
        return result

    ops = {
        # Generator          0
        # Paren              1 
        # Tuple              2, Assoc.Non
        # Lambda             3, Assoc.Right
        Or:       ('or',     4, Assoc.Non),
        And:      ('and',    5, Assoc.Non),
        Not:      ('not',    6, Assoc.Non),
        In:       ('in',     7, Assoc.Non),
        NotIn:    ('not in', 7, Assoc.Non),
        Is:       ('is',     7, Assoc.Non),
        IsNot:    ('is not', 7, Assoc.Non),
        Eq:       ('==',     7, Assoc.Non),
        NotEq:    ('!=',     7, Assoc.Non),
        LtE:      ('<=',     7, Assoc.Non),
        Lt:       ('<',      7, Assoc.Non),
        GtE:      ('>=',     7, Assoc.Non),
        Gt:       ('>',      7, Assoc.Non),
        BitOr:    ('|',      8, Assoc.Left),
        BitXor:   ('^',      9, Assoc.Left),
        BitAnd:   ('&',     10, Assoc.Left),
        LShift:   ('<<',    11, Assoc.Left),
        RShift:   ('>>',    11, Assoc.Left),
        Add:      ('+',     13, Assoc.Left),
        Sub:      ('-',     13, Assoc.Left),
        Mult:     ('*',     14, Assoc.Left),
        Div:      ('/',     14, Assoc.Left),
        FloorDiv: ('//',    14, Assoc.Left),
        Mod:      ('%',     14, Assoc.Left),
        UAdd:     ('+',     15, Assoc.Right),
        USub:     ('-',     15, Assoc.Right),
        Invert:   ('~',     15, Assoc.Right),
        Pow:      ('**',    16, Assoc.Right),
        # Attribute         17, Assoc.Left
        }

    opnames = set(v[0] for v in ops.values())
    opnames.add('if')

    # These nodes in the parse tree have associated suites, and when
    # they are nested they cannot be combined onto one line: for
    # example, "if x:pass" is OK, but "if x:if y:pass" is a syntax
    # error.
    multiliners = [
        ClassDef, For, FunctionDef, If, TryExcept, TryFinally, While, With
        ]

    def comma(self, b=True):
        self.emit(',', b)

    def idchar(self, c):
        return c.isalnum() or c == '_'

    def emit_raw(self, s):
        self.result.append(s)

    def space_needed(self, s):
        if not self.idchar(self.lastchar) or not self.idchar(s[0]):
            return False
        if not self.lastnum:
            return True
        if (self.lastchar in '123456789' and s[0] != 'e'
            or self.lastchar == '0' and self.lastemit != '0' and s[0] != 'e'
            or self.lastemit == '0' and s[0] not in 'beox'):
            return False
        return True

    def emit(self, s, emit=True):
        if emit:
            if self.space_needed(s):
                self.emit_raw(' ')
            self.emit_raw(s)
            self.lastchar = s[-1]
            self.lastemit = s
            self.lastnum = False

    def newline(self):
        if self.lastchar != '\n':
            self.emit('\n')
            if self.depth > 0:
                self.emit_raw(' ' * self.depth * self.indent)

    def visit_alias(self, node):
        self.emit(node.name)
        if node.asname:
            self.emit('as')
            self.emit(node.asname)

    def visit_arguments(self, node):
        i = 0
        for a in node.args:
            self.comma(i)
            self.visit(a)
            if len(node.args) - i <= len(node.defaults):
                self.emit('=')
                self.visit(node.defaults[i - len(node.args)])
            i += 1
        if node.vararg:
            self.comma(i)
            self.emit('*' + node.vararg)
            i += 1
        if node.kwarg:
            self.comma(i)
            self.emit('**' + node.kwarg)
            i += 1
    
    def multiline(self, node):
        return any(isinstance(node, t) for t in self.multiliners)

    def multiline_body(self, body):
        return any(self.multiline(b) for b in body)

    def no_side_effects(self, node):
        # Not exhaustive, but will catch many cases.
        if isinstance(node, (Num, Str, Pass)):
            return True
        if isinstance(node, Expr):
            return self.no_side_effects(node.value)
        if isinstance(node, BinOp):
            return all(map(self.no_side_effects, (node.left, node.right)))
        if isinstance(node, UnaryOp):
            return self.no_side_effects(node.operand)
        if isinstance(node, BoolOp):
            return all(map(self.no_side_effects, node.values))
        if isinstance(node, Compare):
            return all(map(self.no_side_effects, [node.left,] + node.comparators))
        return False

    def visit_body(self, body, colon=True):
        if colon:
            self.emit(':')
        M = not self.joinlines or self.multiline_body(body)
        if M:
            self.depth += 1
            self.newline()
        prev_multiline = False
        statements = 0
        for b in body:
            if self.docstrings and self.no_side_effects(b):
                continue
            cur_multiline = self.multiline(b)
            if not self.joinlines or prev_multiline or cur_multiline:
                self.newline()
            else:
                self.emit(';', statements)
            self.visit(b)
            prev_multiline = cur_multiline
            statements += 1
        if statements == 0:
            self.emit('0')
        if M:
            self.depth -= 1

    def visit_decorators(self, decorators):
        for d in decorators:
            self.newline()
            self.emit('@')
            self.visit(d)
            self.newline()

    def visit_generators(self, generators):
        for g in generators:
            self.emit('for')
            with SavePrecedence(self):
                self.prec = Prec.Paren
                self.visit(g.target)
            self.emit('in')
            with SavePrecedence(self):
                self.prec = Prec.Lambda
                self.visit(g.iter)
                for i in g.ifs:
                    self.emit('if')
                    self.visit(i)

    def visit_orelse(self, node):
        if node.orelse:
            self.newline()
            self.emit('else')
            self.visit_body(node.orelse)

    def visit_Assert(self, node):
        self.emit('assert')
        with SavePrecedence(self, Prec.Tuple):
            self.prec = Prec.Tuple
            self.visit(node.test)
            if node.msg:
                self.comma()
                self.visit(node.msg)

    def visit_Assign(self, node):
        for t in node.targets:
            self.visit(t)
            self.emit('=')
        self.visit(node.value)

    def visit_Attribute(self, node):
        with SavePrecedence(self, Prec.Attribute, Assoc.Left):
            self.prec = Prec.Attribute
            self.assoc = Assoc.Left
            self.operator = '.'
            self.visit(node.value)
            self.emit('.')
            self.emit(node.attr)

    def visit_AugAssign(self, node):
        self.visit(node.target)
        self.emit(self.ops[type(node.op)][0])
        self.emit('=')
        self.visit(node.value)

    def visit_BinOp(self, node):
        name, prec, assoc = self.ops[type(node.op)]
        with SavePrecedence(self, prec, assoc):
            self.prec = prec
            self.assoc = Assoc.Left
            self.operator = name
            self.visit(node.left)
            self.emit(name)
            self.assoc = Assoc.Right
            self.visit(node.right)

    def visit_BoolOp(self, node):
        name, prec, assoc = self.ops[type(node.op)]
        with SavePrecedence(self, prec, assoc):
            self.prec = prec
            self.assoc = Assoc.Left
            self.operator = name
            for i, v in enumerate(node.values):
                self.emit(name, i)
                self.visit(v)
                self.assoc = Assoc.Right

    def visit_Break(self, node):
        self.emit('break')

    def visit_Call(self, node):
        with SavePrecedence(self):
            self.prec = Prec.Attribute
            self.assoc = Assoc.Left
            self.visit(node.func)
            if (not node.kwargs and not node.starargs
                and not node.keywords
                and len(node.args) == 1
                and isinstance(node.args[0], GeneratorExp)):
                self.prec = Prec.Generator
            else:
                self.prec = Prec.Tuple
            self.emit('(')
            i = 0
            for a in node.args:
                self.comma(i)
                self.visit(a)
                i += 1
            for k in node.keywords:
                self.comma(i)
                self.emit(k.arg)
                self.emit('=')
                self.visit(k.value)
                i += 1
            if node.starargs:
                self.comma(i)
                self.emit('*')
                self.visit(node.starargs)
                i += 1
            if node.kwargs:
                self.comma(i)
                self.emit('**')
                self.visit(node.kwargs)
            self.emit(')')

    def visit_ClassDef(self, node):
        self.visit_decorators(node.decorator_list)
        self.emit('class')
        self.emit(node.name)
        if node.bases:
            with SavePrecedence(self):
                self.prec = Prec.Tuple
                self.emit('(')
                for i, b in enumerate(node.bases):
                    self.comma(i)
                    self.visit(b)
                self.emit(')')
        self.visit_body(node.body)

    def visit_Compare(self, node):
        name, prec, assoc = self.ops[type(node.ops[0])]
        with SavePrecedence(self, prec, assoc):
            self.prec = prec
            self.assoc = Assoc.Left
            self.visit(node.left)
            for op, val in zip(node.ops, node.comparators):
                self.emit(self.ops[type(op)][0])
                self.assoc = Assoc.Right
                self.visit(val)

    def visit_Continue(self, node):
        self.emit('continue')

    def visit_Delete(self, node):
        self.emit('del')
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            for i, t in enumerate(node.targets):
                self.comma(i)
                self.visit(t)

    def visit_Dict(self, node):
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            self.emit('{')
            for i, (k, v) in enumerate(zip(node.keys, node.values)):
                self.comma(i)
                self.visit(k)
                self.emit(':')
                self.visit(v)
            self.emit('}')

    def visit_DictComp(self, node):
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            self.emit('{')
            self.visit(node.key)
            self.emit(':')
            self.visit(node.value)
            self.visit_generators(node.generators)
            self.emit('}')

    def visit_Ellipsis(self, node):
        self.emit('...')

    def visit_Exec(self, node):
        self.emit('exec')
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            self.visit(node.body)
            if node.globals:
                self.emit('in')
                self.visit(node.globals)
                if node.locals:
                    self.comma()
                    self.visit(node.locals)

    def visit_ExtSlice(self, node):
        for i, d in enumerate(node.dims):
            self.visit(d)
            self.comma(i == 0 or i + 1 < len(node.dims))

    def visit_For(self, node):
        self.emit('for')
        self.visit(node.target)
        self.emit('in')
        self.visit(node.iter)
        self.visit_body(node.body)
        self.visit_orelse(node)

    def visit_FunctionDef(self, node):
        self.visit_decorators(node.decorator_list)
        self.emit('def')
        self.emit(node.name)
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            self.emit('(')
            self.visit(node.args)
            self.emit(')')
        self.visit_body(node.body)

    def visit_GeneratorExp(self, node):
        with SavePrecedence(self, Prec.Paren):
            self.prec = Prec.Tuple
            self.visit(node.elt)
            self.visit_generators(node.generators)

    def visit_Global(self, node):
        self.emit('global')
        for i, n in enumerate(node.names):
            self.comma(i)
            self.emit(n)

    def visit_If(self, node):
        self.emit('if')
        while True:
            self.visit(node.test)
            self.visit_body(node.body)
            if len(node.orelse) != 1 or not isinstance(node.orelse[0], If):
                break
            self.newline()
            self.emit('elif')
            node = node.orelse[0]
        self.visit_orelse(node)

    def visit_IfExp(self, node):
        with SavePrecedence(self, Prec.Lambda, Assoc.Right):
            self.prec = Prec.Or
            self.visit(node.body)
            self.emit('if')
            self.visit(node.test)
            if node.orelse:
                self.emit('else')
                self.prec = Prec.Lambda
                self.assoc = Assoc.Right
                self.visit(node.orelse)

    def visit_Import(self, node):
        self.emit('import')
        for i, n in enumerate(node.names):
            self.comma(i)
            self.visit(n)

    def visit_ImportFrom(self, node):
        self.emit('from')
        if node.level:
            self.emit('.' * node.level)
        if node.module:
            self.emit(node.module)
        self.emit('import')
        for i, n in enumerate(node.names):
            self.comma(i)
            self.visit(n)
            if node.module == '__future__' and n.name == 'unicode_literals':
                self.unicode_literals = True

    def visit_Lambda(self, node):
        with SavePrecedence(self, Prec.Lambda, Assoc.Right):
            self.prec = Prec.Lambda
            self.assoc = Assoc.Right
            self.emit('lambda')
            self.visit_arguments(node.args)
            self.emit(':')
            self.visit(node.body)

    def visit_List(self, node):
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            self.emit('[')
            for i, e in enumerate(node.elts):
                self.comma(i)
                self.visit(e)
            self.emit(']')

    def visit_ListComp(self, node):
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            self.emit('[')
            self.visit(node.elt)
            self.visit_generators(node.generators)
            self.emit(']')

    def visit_Module(self, node):
        if node.body:
            self.visit_body(node.body, colon=False)

    def visit_Name(self, node):
        self.emit(node.id)

    def visit_Num(self, node):
        s = repr(node.n)
        sign = ''
        prec = Prec.Attribute
        if self.selftest and self.operator == '-':
            prec = 14           # -(1), not -1: see issue #38.
        if s[0] == '-':
            sign = '-'
            prec = 16
        with SavePrecedence(self, prec, Assoc.Right):
            if isinstance(node.n, float) and isinf(node.n):
                self.emit(sign + '1e400')
            else:
                self.emit(s)
        self.lastnum = True

    def visit_Pass(self, node):
        self.emit('pass' if self.selftest else '0')

    def visit_Print(self, node):
        self.emit('print')
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            i = 0
            if node.dest:
                self.emit('>>')
                self.visit(node.dest)
                i = 1
            for v in node.values:
                self.comma(i)
                self.visit(v)
                i += 1
            self.emit(',', not node.nl)

    def visit_Raise(self, node):
        self.emit('raise')
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            if node.type:
                self.visit(node.type)
            if node.inst:
                self.comma()
                self.visit(node.inst)
            if node.tback:
                self.comma()
                self.visit(node.tback)

    def visit_Repr(self, node):
        self.emit('`')
        self.visit(node.value)
        self.emit('`')

    def visit_Return(self, node):
        self.emit('return')
        if node.value:
            self.visit(node.value)

    def visit_Set(self, node):
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            self.emit('{')
            for i, e in enumerate(node.elts):
                self.comma(i)
                self.visit(e)
            self.emit('}')            

    def visit_SetComp(self, node):
        with SavePrecedence(self):
            self.prec = Prec.Tuple
            self.emit('{')
            self.visit(node.elt)
            self.visit_generators(node.generators)
            self.emit('}')

    def visit_Slice(self, node):
        if node.lower:
            self.visit(node.lower)
        self.emit(':')
        if node.upper:
            self.visit(node.upper)
        if node.step:
            self.emit(':')
            if not isinstance(node.step, Name) or node.step.id != 'None':
                self.visit(node.step)

    _escape_sequences = [
        ('\a', r'\a'),
        ('\b', r'\b'),
        ('\f', r'\f'),
        ('\r', r'\r'),
        ('\t', r'\t'),
        ('\v', r'\v'),
        ]
    _escape_set = set(e[0] for e in _escape_sequences)

    def encode_string(self, s, escapes=True, quotes=None, error='backslashreplace'):
        if escapes:
            s = s.replace('\\', '\\\\')
            for e, f in self._escape_sequences:
                s = s.replace(e, f)
            if quotes:
                if len(quotes) == 1:
                    s = s.replace('\n', r'\n')
                elif s and s[-1] == quotes[0]:
                    s = s[:-1] + '\\' + s[-1]
                s = s.replace(quotes, '\\' + quotes)
                
        def escape(m):
            c = ord(m.group(0))
            if c < 8 and (m.group(1) == '' or not m.group(1).isdigit()):
                if c == 0:
                    return r'\0'
                else:
                    return r'\0{0:o}'.format(c)
            return r'\x{0:02x}'.format(c)
        if isinstance(s, unicode):
            s = re.sub('[\x00-\x1f](?=(.?))', escape, s)
            return s.encode(self.encoding, error)
        else:
            return re.sub('[\x00-\x1f\x7f-\xff](?=(.?))', escape, s)

    def shortest_string_repr(self, s):
        """
        Return the shortest representation of the string s suitable for a
        Python source file in self.encoding. Generates up to eight ways
        of representing the string and picks the shortest.
        """
        if self.unicode_literals:
            prefix = 'b' * isinstance(s, str)
        else:
            prefix = 'u' * isinstance(s, unicode)
        cand = []               # List of candidate representation.

        # The constraints on r-prefixed strings are really quite tight:
        #
        # 1. Backslash-replacement must add no more backslashes when we
        #    come to encode the output. (Otherwise we'll get something
        #    like r'\xa0' which will be wrongly interpreted.)
        # 2. The string contains none of the six escape sequences in
        #    _escape_set.
        # 3. The string does not end with a backslash.
        #
        # Even if these three constraints are all met, we might still be
        # unable to use a particular set of quotation marks: no set of
        # quotes can be used if that set appears in the string, and
        # newlines may not appear in single- or double-quoted strings.

        s1 = self.encode_string(s, escapes=False, error='ignore')
        s2 = self.encode_string(s, escapes=False)
        if (s.count('\\') == s1.count('\\')
            and (prefix != 'u' or '\\u' not in s2 and '\\U' not in s2)
            and not set(s) & self._escape_set
            and s and s[-1] != '\\'):
            for q in ("'''", '"""') + ("'", '"') * ('\n' not in s):
                if q not in s and not (s and q[0] == s[-1]):
                    cand.append("{0}r{1}{2}{1}".format(prefix, q, s2))

        # Ordinary strings are easy.
        for q in ("'''", '"""', "'", '"'):
            s_encoded = self.encode_string(s, True, q)
            cand.append("{0}{1}{2}{1}".format(prefix, q, s_encoded))
        return min(cand, key=len)

    def visit_Str(self, node):
        self.emit(self.shortest_string_repr(node.s))

    def visit_Subscript(self, node):
        with SavePrecedence(self, Prec.Attribute, Assoc.Left):
            self.prec = Prec.Attribute
            self.assoc = Assoc.Left
            self.visit(node.value)
            self.emit('[')
            self.prec = Prec.Tuple
            self.visit(node.slice)
            self.emit(']')            

    def visit_TryExcept(self, node):
        self.emit('try')
        self.visit_body(node.body)
        for h in node.handlers:
            self.newline()
            self.emit('except')
            with SavePrecedence(self):
                self.prec = Prec.Tuple
                if h.type:
                    self.visit(h.type)
                if h.name:
                    self.comma()
                    self.visit(h.name)
            self.visit_body(h.body)
        self.visit_orelse(node)

    def visit_TryFinally(self, node):
        if len(node.body) == 1 and isinstance(node.body[0], TryExcept):
            self.visit(node.body[0])
        else:
            self.emit('try')
            self.visit_body(node.body)
        if node.finalbody:
            self.newline()
            self.emit('finally')
            self.visit_body(node.finalbody)

    def visit_Tuple(self, node):
        with SavePrecedence(self, Prec.Tuple, force=not node.elts):
            self.prec = Prec.Tuple
            for i, e in enumerate(node.elts):
                self.comma(i)
                self.visit(e)
            if len(node.elts) == 1:
                self.comma()

    def visit_UnaryOp(self, node):
        name, prec, assoc = self.ops[type(node.op)]
        with SavePrecedence(self, prec, assoc):
            self.prec = prec
            self.assoc = assoc
            self.operator = name
            self.emit(name)
            self.visit(node.operand)

    def visit_While(self, node):
        self.emit('while')
        self.visit(node.test)
        self.visit_body(node.body)
        self.visit_orelse(node)

    def visit_With(self, node):
        self.emit('with')
        while True:
            self.visit(node.context_expr)
            if node.optional_vars:
                self.emit('as')
                with SavePrecedence(self, Prec.Tuple):
                    self.prec = Prec.Tuple
                    self.visit(node.optional_vars)
            if len(node.body) == 1 and isinstance(node.body[0], With):
                self.comma()
                node = node.body[0]
            else:
                break
        self.visit_body(node.body)

    def visit_Yield(self, node):
        with SavePrecedence(self, Prec.Tuple):
            self.emit('yield')
            if node.value:
                self.visit(node.value)

def serialize_ast(tree, **kwargs):
    """
    Serialize an abstract syntax tree according to the options and
    return an encoded string. Takes keyword arguments:

    docstrings -- Remove docstrings and other statements with no side
                  effects (default: False)
    encoding   -- Encoding for the result (default: 'latin1')
    indent     -- Number of spaces for each indentation level (default: 1)
    joinlines  -- Join lines if possible (default: True)
    selftest   -- Reparse the result and check that it's identical to the
                  tree (default: True)
    """
    return SerializeVisitor(**kwargs).serialize(tree)

class FindReserved(NodeVisitor):
    def reserve(self, tree):
        import __builtin__
        self.reserved = set(__builtin__.__dict__)
        self.visit(tree)
        return self.reserved

    def reserve_import(self, n):
        self.reserved.add(n)
        try:
            self.reserved.update(dir(load_module(n, *find_module(n))))
        except:
            pass

    def visit_alias(self, node):
        self.reserved.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if (len(node.targets) == 1 and isinstance(node.targets[0], Name)
            and node.targets[0].id == '__all__'):
            expr = copy_location(Expression(node.value), node)
            self.reserved.update(eval(compile(expr, '<string>', 'eval')))
        self.generic_visit(node)

    def visit_Attribute(self, node):
        self.reserved.add(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node):
        for k in node.keywords:
            self.reserved.add(k.arg)
        self.generic_visit(node)

    def visit_Import(self, node):
        for i in node.names:
            self.reserved.add(i.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.reserve_import(node.module)
        self.generic_visit(node)

def reserved_names_in_ast(tree):
    """
    Make a best effort to find reserved names (that is, names that
    cannot be changed without changing the meaning of the program) in an
    abstract syntax tree. Return the set of words found.
    """
    return FindReserved().reserve(tree)

class Rename(NodeTransformer):
    def __init__(self, mapping):
        self.mapping = mapping

    def rename(self, name):
        return self.mapping.get(name, name)

    def visit_alias(self, node):
        node.asname = self.rename(node.asname)
        return self.generic_visit(node)

    def visit_Call(self, node):
        for k in node.keywords:
            k.arg = self.rename(k.arg)
        return self.generic_visit(node)

    def visit_ClassDef(self, node):
        node.name = self.rename(node.name)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        node.name = self.rename(node.name)
        return self.generic_visit(node)

    def visit_Global(self, node):
        for i, n in enumerate(node.names):
            node.names[i] = self.rename(n)
        return self.generic_visit(node)        

    def visit_Name(self, node):
        node.id = self.rename(node.id)
        return self.generic_visit(node)

class FindNames(NodeVisitor):
    def newname(self):
        result = [0, self.count]
        self.count += 1
        return result

    def find(self, tree):
        """
        Find names in an abstract syntax tree and return a dictionary
        mapping names to pairs [n, m] where n is the number of
        occurrences of the name, and m is the number of distinct names
        that appear prior to this one.
        """
        from collections import defaultdict
        self.name = defaultdict(self.newname)
        self.count = 0
        self.visit(tree)
        return self.name

    def learn(self, name):
        self.name[name][0] += 1

    def visit_alias(self, node):
        self.learn(node.asname)
        self.generic_visit(node)

    def visit_Call(self, node):
        for k in node.keywords:
            self.learn(k.arg)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.learn(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.learn(node.name)
        self.generic_visit(node)

    def visit_Global(self, node):
        for n in node.names:
            self.learn(n)
        self.generic_visit(node)        

    def visit_Name(self, node):
        self.learn(node.id)
        self.generic_visit(node)

letters = ascii_lowercase + ascii_uppercase
letters_len = len(letters)
def make_name(n):
    """Return the nth name."""
    name = ''
    n += 1
    while n:
        n -= 1
        name = letters[n % letters_len] + name
        n //= letters_len
    return name

def rename_ast(tree, reserved=set()):
    """
    Change all names in an abstract syntax tree, except for a set of
    reserved names. The new names are as short as possible.
    """
    from keyword import iskeyword
    names = FindNames().find(tree)
    mapping = dict()
    n = [0] * 3
    sorted_names = sorted(((i, j, k) for k, (i, j) in names.items()),
                          key = lambda (i, j, k): (-i, j, k))
    for _, _, name in sorted_names:
        if name is None or name[:2] == name[-2:] == '__' or name in reserved:
            continue
        underscores = name.startswith('_') + name.startswith('__')
        while name not in mapping:
            newname = '_' * underscores + make_name(n[underscores])
            n[underscores] += 1
            if newname not in reserved and not iskeyword(newname):
                mapping[name] = newname
    Rename(mapping).visit(tree)

def detect_encoding(filename):
    """
    Detect input encoding of Python source code by looking for the
    encoding cookie on the first or second line of the file, as
    specified by PEP 263. Return a pair whose first element is the
    encoding (or 'latin1' if none was found), and whose second element
    is text that must be copied to the transformed file: the #! line, if
    any, and the line containing the encoding cookie, if any.
    """
    preserve = ''
    coding_re = re.compile("#.*coding[:=]\s*([-\w.]+)")
    with open(filename, 'rb') as f:
        first = f.readline()
        m = coding_re.search(first)
        if first[:2] == '#!' or m:
            preserve = first
        if not m:
            second = f.readline()
            m = coding_re.search(second)
            if m:
                preserve += second
        encoding = m.group(1) if m else 'latin1'
        return encoding, preserve

def main():
    # Handle command-line arguments.
    import optparse
    p = optparse.OptionParser(usage="usage: %prog [options] [-o OUTPUT] FILE",
                              version='%prog {0}'.format(__version__))
    p.add_option('--output', '-o', 
                 help="output file (default: stdout)")
    p.add_option('--docstrings', '-D', 
                 action='store_true', default=False,
                 help="remove docstrings and other statements with no side effects "
                 "(implies --noselftest)")
    p.add_option('--rename', '-R', 
                 action='store_true', default=False,
                 help="aggressively rename non-preserved variables")
    p.add_option('--indent', '-i', 
                 type='int', default=1,
                 help="number of spaces per indentation level")
    p.add_option('--preserve', '-p', 
                 help="preserve words from renaming (separate by commas)")
    p.add_option('--nojoinlines', dest='joinlines', 
                 action='store_false', default=True, 
                 help="put each statement on its own line")
    p.add_option('--noselftest', dest='selftest', 
                 action='store_false', default=True, 
                 help="skip the self-test")
    p.add_option('--debug', 
                 action='store_true', default=False,
                 help="dump the parse tree")
    opts, args = p.parse_args()
    if len(args) != 1:
        p.error("missing FILE")

    # Read input and minify.
    encoding, preserve = detect_encoding(args[0])
    tree = parse(open(args[0]).read())
    if opts.debug:
        stderr.write(dump(tree))
        stderr.write('\n')
    if opts.rename:
        r = reserved_names_in_ast(tree)
        if opts.preserve:
            r.update(opts.preserve.split(','))
        rename_ast(tree, r)
    minified = serialize_ast(tree, encoding=encoding, **opts.__dict__)

    # Output.
    if opts.output:
        out = open(opts.output, 'wb')
    else:
        out = stdout
    out.write(preserve)
    out.write(minified)
    out.write('\n')

if __name__ == '__main__':
    main()

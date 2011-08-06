#!/usr/bin/env python

from ast import parse
import minipy
import os
from subprocess import Popen, PIPE
import unittest
from sys import executable

class MinipyTests(unittest.TestCase):
    testdir = 'test'

    def testExpressions(self):
        with open(os.path.join(self.testdir, 'expressions.txt')) as f:
            tests = f.read().splitlines()
            for t in tests:
                src, out = t.split(' -> ')
                self.assertEqual(minipy.serialize_ast(parse(src)), out)

    def testCases(self):
        for f in os.listdir(self.testdir):
            args = [executable, minipy.__file__]
            components = f.split('.')
            if len(components) == 3:
                for c in components[1]:
                    a = {
                        'J': '--nojoinlines',
                        'D': '--docstrings',
                        'R': '--rename',
                        '4': '--indent=4',
                        }.get(c)
                    if a:
                        args.append(a)
                args.append(os.path.join(self.testdir, f))
                pipe = Popen(args, stdout=PIPE)
                output, _ = pipe.communicate()
                resultfile = os.path.join(self.testdir, components[0] + ".py")
                self.assertEqual(output, open(resultfile).read())

if __name__ == '__main__':
    unittest.main()

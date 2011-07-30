#!/usr/bin/env python

import ast
import minipy
import os
import subprocess
import unittest

class MinipyTests(unittest.TestCase):
    def testExpressions(self):
        tests = open('test/expressions.txt').read().splitlines()
        for t in tests:
            src, out = t.split(' -> ')
            self.assertEqual(minipy.serialize_ast(ast.parse(src)), out)

    def testCases(self):
        testdir = 'test'
        for f in os.listdir(testdir):
            args = ['./minipy.py']
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
                args.append(os.path.join(testdir, f))
                pipe = subprocess.Popen(args, 
                                        stdout=subprocess.PIPE)
                output, _ = pipe.communicate()
                resultfile = os.path.join(testdir, components[0] + ".py")
                self.assertEqual(output, open(resultfile).read())

if __name__ == '__main__':
    unittest.main()

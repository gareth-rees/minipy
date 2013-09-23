#!/usr/bin/env python

from ast import parse
import minipy
import os
from StringIO import StringIO
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
            filename = os.path.join(self.testdir, f)
            args = [executable, minipy.__file__]
            kwargs = dict()
            components = f.split('.')
            if len(components) == 3:
                for c in components[1]:
                    a = {
                        'J': ('--nojoinlines', dict(joinlines=False)),
                        'D': ('--docstrings', dict(docstrings=True)),
                        'R': ('--rename', dict(rename=True)),
                        '4': ('--indent=4', dict(indent=4)),
                        }.get(c)
                    if a:
                        args.append(a[0])
                        kwargs.update(a[1])

                # Run this test case via the script interface
                args.append(filename)
                pipe = Popen(args, stdout=PIPE)
                output, _ = pipe.communicate()
                resultfile = os.path.join(self.testdir, components[0] + ".py")
                correct = open(resultfile).read()
                self.assertEqual(output, correct)

                # Run this test case via the Python interface
                output = StringIO()
                minipy.minify(filename, output=output, **kwargs)
                output.seek(0)
                self.assertEqual(output.read(), correct)


if __name__ == '__main__':
    unittest.main()

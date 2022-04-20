======
minipy
======
a Python 3 minifier
by Gareth Rees <http://garethrees.org/>
(python3 port by Joel Martin <https://github.com/kanaka>)


Introduction
------------
**minipy** is a minifier for Python 3. It rewrites Python 3 source code in a
way that preserves the meaning of the code while reducing it in
size. For example::

    $ cat fib.py
    cache = {0: 0, 1: 1, 2: 1, 3: 2}
    def fibonacci(n):
        """Return the nth Fibonacci number."""
        if n not in cache:
            a = n // 2
            r = n % 2
            m = (r * 2) - 1
            cache[n] = fibonacci(a + 1) ** 2 + m * fibonacci(a + r - 1) ** 2
        return cache[n]

    $ minipy --rename --docstrings fib.py
    b={0:0,1:1,2:1,3:2}
    def c(a):
     if a not in b:d=a//2;e=a%2;f=e*2-1;b[a]=c(d+1)**2+f*c(d+e-1)**2
     return b[a]


Command line
------------
::

    Usage: minipy [options] [-o OUTPUT] FILE

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -o OUTPUT, --output=OUTPUT
                            output file (default: stdout)
      -D, --docstrings      remove docstrings and other statements with no side
                            effects (implies --noselftest)
      -R, --rename          aggressively rename non-preserved variables
      -i INDENT, --indent=INDENT
                            number of spaces per indentation level
      -p PRESERVE, --preserve=PRESERVE
                            preserve words from renaming (separate by commas)
      --nojoinlines         put each statement on its own line
      --noselftest          skip the self-test
      --debug               dump the parse tree


The self-test
-------------
Generating minified source code without accidentally changing the
meaning is tricky: see the `list of issues`_ for many awkward cases
that had to be fixed. Therefore, in its default operating mode, minipy
performs a “self-test”: it takes the minified code, re-parses it, and
asserts that the parse tree for the minified code is identical to the
parse tree for the original code. If the self-test passes, then you can
be highly confident that minipy has not changed the meaning of your
code.

In order to pass the self-test, minipy must eschew a few changes to the
code that result in harmless changes to the parse tree. These changes
are:

* Replacing ``pass`` with ``0``.
* Replacing ``-(1)`` with ``-1``.

You can use the ``--noselftest`` option to enable these changes, but by
disabling the self-test you accept a small risk of a bug in minipy
changing the meaning of your code.

The optional transformations ``--rename`` and ``--docstrings`` can’t be
combined with the self-test, so these options imply ``--noselftest``.

Please report_ all self-test failures, attaching the code that causes
the failure.


Renaming
--------
Python’s use of introspection and duck typing means that it is not
possible to change names in a program without risk of changing the
meaning. The ``--rename`` option to minipy therefore makes a “best attempt”
to discover names that need to be preserved, but does not guarantee
anything. Use at your own risk!

The following names are preserved when renaming:

* Names specified on the command-line via the ``--preserve`` option
  (write ``--preserve=name1,name2,name3`` to preserve more than one name).
* Built-in names (``abs``, ``all``, ``any``, ``apply``, ...).
* Any name used as an attribute (``.join``, ``.index``, ``.copy``, ``.sort``, ...).
* Any name starting and ending with two underscores.
* Any name exported by a module in a ``from module import *`` statement.
* Any name in the list assigned to the ``__all__`` global variable.


License
-------
minipy is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the `GNU
General Public License`_ for more details.


.. _list of issues: https://github.com/gareth-rees/minipy/issues?state=closed
.. _report: https://github.com/gareth-rees/minipy/issues/new
.. _GNU General Public License: http://www.gnu.org/copyleft/gpl.html

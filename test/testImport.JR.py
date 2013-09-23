# If there are no uses, don't apply the transformation.
import datetime

# For a long enough name, a single use is enough to justify the transformation.
import multiprocessing
multiprocessing.Pipe

# A three-letter module needs three uses to justify it.
import sys
sys.stdin, sys.stdout
import cgi
cgi.parse, cgi.parse_qs, cgi.parse_qsl

# A two-letter module needs six uses to justify it.
import os
os.abort, os.access, os.altsep, os.chdir, os.chflags
import io
io.IOBase, io.RawIOBase, io.FileIO, io.BytesIO, io.StringIO, io.BufferedIOBase

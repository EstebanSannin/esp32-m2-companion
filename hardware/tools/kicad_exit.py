"""Exit KiCad's bundled Python without interpreter finalization.

KiCad 9.0.9's macOS Python 3.9 segfaults in Py_FinalizeEx (GC over pcbnew
SWIG objects) AFTER a script has finished - harmless to results, but macOS
pops a "Python quit unexpectedly" dialog every time. Every pcbnew script
ends through run()/hard_exit() so finalization never runs.
"""

import os
import sys
import traceback


def hard_exit(code=0):
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


def run(fn, *args):
    try:
        rc = fn(*args)
    except SystemExit as e:
        hard_exit(e.code if isinstance(e.code, int) else 1)
    except BaseException:
        traceback.print_exc()
        hard_exit(1)
    hard_exit(rc if isinstance(rc, int) else 0)

"""Work around a Windows DLL-name collision between Isaac Sim/Kit's own native plugins and h5py's
bundled hdf5.dll/z.dll: whichever DLL with a given base name loads into the process FIRST wins for
every later load request with that same name. Importing h5py here, before `from isaaclab.app import
AppLauncher` (inside the target script) ever starts the Kit process and its native extensions, makes
h5py's own (correct) hdf5.dll/z.dll the one that's already resident when anything else in the process
later asks Windows for a same-named DLL.

Does not modify train.py/play.py or any tracked file. Usage:
    python preload_h5py_and_run.py <target_script.py> [args...]
"""
import os
import runpy
import sys

import h5py  # noqa: F401  (import only for its side effect of loading hdf5.dll/z.dll first)

target = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(target)))
runpy.run_path(target, run_name="__main__")

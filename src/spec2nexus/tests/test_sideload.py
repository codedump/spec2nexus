"""
Tests for the sideload module.

ACHTUNG, 
"""

from ._core import testpath, file_from_tests
from .. import sideload

import pytest

from pprint import pprint

def test_get_image_list():
    files = sideload.get_image_list(basedir=file_from_tests("fileitr"),
                                    scan=23,
                                    datadir_fmt="{basedir}/{scan}",
                                    datafile_fmt="{}_{scan}_{idx}.{}")

    print ("\nFiles, sorted:\n")
    pprint (files)

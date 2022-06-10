#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Support code for the sideloading of external data (e.g. TIFF files
not referenced in the original SPEC file).

The idea is that the main `spec2nexus` application offers a `--sideload`
switch which triggers this functionality. Argument parsing for everything
after that is passed to this module. This consumes all arguments it
encounters (specific stuff to sideloading) and finishes / passes parsing
control to the main application once the command line finishes, or once
it encounters parameters it doesn't understand.

The general usage pattern is something along the lines of:

  $ spec2nexus experiment.spec --sideload \
             --path 'pilatus/S{scan:05}/experiment_{scan}_{idx}.tif' \
             --h5store 'images/img-{idx:03}'

Relative paths on the hard disk (e.g. `pilatus/...`) are being interpreted
as relative to the SPEC file, while relative paths within the HDF5/Nexus
file (e.g. `images/img...`) are taken relative to the current scan
Nexus group (i.e. actually `/S23/images/img...` for scan no. 23).

The limitation is that all data that belongs to a specific scan must be
flat inside a single directory (i.e. no subdirectories).

Dependencies:
   - tifffile (for loading TIFF images)
   - parse (for more advanced string / filename / pattern parsing)
   - re (for simpler regex-based filename / pattern parsing)
   - os.scandir (for scanning directory contents; no, really!...)
"""

import tifffile
import parse
import re
import argparse

from os import scandir
from os import path


def get_image_list(basedir,
                   scan=None,
                   datadir_fmt="{basedir}",
                   datafile_fmt="{}_{idx}.{}"):
    '''
    Returns a possibly sorted list of files (full path!) that match
    a specific pattern. The data files are expected to be somerhere
    at `{basedir}/{datadir}/{datafile}`, with the caveats
    specified below.
    
    Parameters:
    
      - `basedir`: The base directory where the data is to be found.
        Generally, this is expected to be the dirname part of the
        SPEC file path.
    
      - `scan`: The SPEC scan number/index. This is used to construct
        a scan-specific data dir based off of `basepath`, using `datadir`
        as a format template. If `scan_nr` is set to None (default),
        or `datadir` is set to None, then all the data is expected to
        be in `basepath`.

      - `datadir_fmt`: Format template for the data directory. Defaults
        to `{basedir}`, which means that data files are to be found
        in the same directory as the SPEC file.
    
      - `datafile_fmt`: Format template for the data file, based on
        `{basedir}/{datadir}`. This parameter essentially
        defines how to decompose the file name in order to find and extract
        the `idx` variable. The general idea is that the `idx` part of the
        filename symbolizes a numerical index of a partial scan, and the sole
        purpose of this parameter is to extract that information and allow
        for numerical sorting. This parameter *must* be defined and *must*
        match your data. You can use something very simple, e.g.
        `datafmt="{}"` in which case your data will be found in the same
        folder as the SPEC file and won't be sorted.
    

    The following format variables are defined for the context of this
    function. Please keep in mind that some of these variables come from
    upper layers (e.g. `scan`), while others are being defined as the
    inner loop of this function progresses:
    
      - `scan`: The SPEC scan number (see above)

      - `idx`: The index of the current data file, as parsed from
        the file name (initially undefined, changes as the loop
        progresses).

      - `ext`: File name extension of the file currently being processed
        (initially undefined, may change as the loop progresses)

    
    The function returns a list of full absolute (!) file paths that match
    the `datafile_fmt` pattern. The list is sorted numerically by the `idx`
    parameter, if that parameter is part of the parsing result.
    Any file in the specified dir that does not match the pattern
    will be silently disregarded.
    '''

    imgdir = datadir_fmt.format(basedir=basedir, scan=scan)

    try:
        tuples = []
        
        for f in scandir(imgdir):
            r = parse.parse(datafile_fmt, f.name)
            
            if r is None:
                continue

            try:
                idx = int(r.named["idx"])
                
            except ValueError:
                # 'idx' is not a number, fall back to string
                idx = r.named["idx"]
                
            except KeyError:
                # 'idx' was not even part of the format string,
                # fall back to a bogus sorting key
                idx = 0
                
            tuples.append((f.path, int(r.named["idx"])))

        files_sorted = [ f[0] for f in sorted(tuples, key=lambda t: t[1])]

        return files_sorted
        
    except FileNotFoundError as e:
        raise e

    except IndexError as e:
        raise e    



def setup_arg_parser(top_action):
    '''
    Returns an argparse ArgumentParser for the sideload functionality.
    The upper layer is responsible for embedding this into the main
    application's parser.

    Parameters:
      - `top_action`: The top level parser action object that
        is able to add a subparser. Typically, this object
        is obtained by calling `parser.add_subparsers()`.
    '''

    sub = top_action.add_parser('sideload', help="Loads data from external files "
                                "unreferenced by the SPEC file")
    
    sub.add_argument('--base', action="store", dest="base_dir",
                     help="Base dir for the data filename, defaults to the directory of the SPEC file")

    sub.add_argument('--dirfmt', action="store", dest="dirfmt",
                     help="Format template for the directory component of "
                     "the data files. Can use a number of variables for formatting,
                     like `{basedir}' for the SPEC file directory and `{scan}' for "
                     "the SPEC scan number. Defaults to \"{basedir}\", meaning that "
                     "data files are expected to be found alongside the SPEC file.")

    sub.add_argument('--filefmt', action="store", dest="filefmt",
                     help="Format template for the filename component of the data files. "
                     "In addition to the formatting variables of `--dirfmt', it also "
                     "accepts `{idx}' as variable, which is a local counter of the "
                     "current dataset index. Defaults to \"{}_{scan}_{idx}.{}\", matching "
                     "a possible filename of the form `example_23_1.tiff', e.g. for scan "
                     "#23.")

    sub.add_argument('--destfmt', action="store", dest="h5dest",
                     help="Format template for the destination object name within "
                     "the HDF5 Nexus file. If the path is relative, it's assumed to be "
                     "relative to the 'Sxxx' section of the HDF file that represents "
                     "the current SPEC scan number. Accepts variables like `{idx}' and "
                     "`{scan}' for the scan number and the dataset index, respectively. "
                     "Each component of the path is expected to have the form 'name[:NX-type]', "
                     "with nonexistent components being idempotently created if they don't exist. "
                     "Defaults to \"sideload:NXdata/data-{idx}\", meaning that sideloaded data "
                     "will be stored in an NXdata typed folder called 'sideload', with a name "
                     "that reflects their datafile index.".)

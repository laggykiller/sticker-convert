#!/usr/bin/env python3

'''
Adapted from https://gitlab.com/mattbas/python-lottie/-/raw/master/bin/lottie_convert.py
'''

import sys
import os
import argparse
from lottie.exporters import exporters
from lottie.importers import importers
from lottie.utils.stripper import float_strip, heavy_strip
from lottie import __version__

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    conflict_handler='resolve'
)

group = importers.set_options(parser)

def print_dep_message(loader):
    if not loader.failed_modules:
        return

    sys.stderr.write("Make sure you have the correct dependencies installed\n")

    for failed, dep in loader.failed_modules.items():
        sys.stderr.write("For %s install %s\n" % (failed, dep))

def lottie_convert(infile, outfile, input_format=None, output_format=None, sanitize=False, optimize=1, fps=None, width=None, height=None, i_options={}, o_options={}):
    ns, unknown = parser.parse_known_args()

    importer = None
    suf = os.path.splitext(infile)[1][1:]
    for p in importers:
        if suf in p.extensions:
            importer = p
            break

    if input_format:
        importer = None
        for p in importers:
            if p.slug == input_format:
                importer = p
                break
    if not importer:
        print("Unknown importer")
        print_dep_message(importers)
        return False

    exporter = exporters.get_from_filename(outfile)
    if output_format:
        exporter = exporters.get(output_format)

    if not exporter:
        print("Unknown exporter")
        print_dep_message(exporters)
        return False

    for opt in importer.extra_options:
        i_options[opt.name] = getattr(ns, opt.nsvar(importer.slug))
    an = importer.process(infile, **i_options)

    if fps:
        an.frame_rate = fps

    if width or height:
        if not width:
            width = an.width * height / an.height
        if not height:
            height = an.height * width / an.width
        an.scale(width, height)

    if optimize == 1:
        float_strip(an)
    elif optimize >= 2:
        heavy_strip(an)

    exporter.process(an, outfile, **o_options)

    return True
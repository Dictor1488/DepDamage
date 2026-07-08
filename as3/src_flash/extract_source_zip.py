# -*- coding: utf-8 -*-
"""
Extract vehicle marker AS3 source into as3/src_flash/src.

Usage from repo root:
    python as3/src_flash/extract_source_zip.py path/to/vehicle_marker_as3_source_patch.zip

This script is intentionally source-only. It does not accept or install a prebuilt SWF.
"""

from __future__ import print_function

import os
import shutil
import sys
import zipfile


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC_FLASH = os.path.join(ROOT, 'as3', 'src_flash')
DEST_SRC = os.path.join(SRC_FLASH, 'src')


def main():
    if len(sys.argv) != 2:
        print('Usage: python as3/src_flash/extract_source_zip.py path/to/vehicle_marker_as3_source_patch.zip')
        return 2

    zip_path = os.path.abspath(sys.argv[1])
    if not os.path.isfile(zip_path):
        print('Source ZIP not found: %s' % zip_path)
        return 2

    if os.path.isdir(DEST_SRC):
        shutil.rmtree(DEST_SRC)
    os.makedirs(DEST_SRC)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if not name.startswith('src/') or name.endswith('/'):
                continue
            rel = name[len('src/'):]
            if not rel:
                continue
            out_path = os.path.join(DEST_SRC, rel.replace('/', os.sep))
            out_dir = os.path.dirname(out_path)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir)
            with open(out_path, 'wb') as fh:
                fh.write(zf.read(name))

    print('Extracted AS3 source to: %s' % DEST_SRC)
    return 0


if __name__ == '__main__':
    sys.exit(main())

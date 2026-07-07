# -*- coding: utf-8 -*-
from __future__ import print_function

import base64
import pathlib


def decode_file(path):
    path = pathlib.Path(path)
    out = path.with_suffix('')
    data = path.read_text(encoding='ascii').strip()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(data))
    path.unlink()
    print('decoded', path, '->', out)


if __name__ == '__main__':
    root = pathlib.Path('resources/in')
    if root.is_dir():
        for path in root.rglob('*.b64'):
            decode_file(path)

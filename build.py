# -*- coding: utf-8 -*-
"""Minimal WoT .wotmod packer for DepDamage."""

from __future__ import print_function

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile


def read_config():
    with open('build.json', 'r') as fh:
        return json.load(fh)


def copytree(src, dst, ignore=None):
    src_path = pathlib.Path(src)
    dst_path = pathlib.Path(dst)
    if not src_path.is_dir():
        return
    dst_path.mkdir(parents=True, exist_ok=True)
    ignored = set()
    if ignore:
        ignored = set(ignore(str(src_path), os.listdir(str(src_path))))
    for item in src_path.iterdir():
        if item.name in ignored:
            continue
        target = dst_path / item.name
        if item.is_dir():
            copytree(str(item), str(target), ignore)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(item), str(target))


def zip_dir(src, dst):
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_STORED) as zf:
        for root, dirs, files in os.walk(src):
            for filename in files:
                full = pathlib.Path(root) / filename
                arc = full.relative_to(src).as_posix()
                zf.write(str(full), arc)


def compile_python(pyexe):
    if not pathlib.Path('python').is_dir():
        return
    for path in pathlib.Path('python').rglob('*.py'):
        print('compile', path)
        subprocess.call([pyexe, '-m', 'py_compile', str(path)])


def build_flash(cfg):
    mxmlc = cfg.get('software', {}).get('mxmlc') or ''
    flex_sdk = cfg.get('software', {}).get('flex_sdk') or ''
    if not mxmlc and flex_sdk:
        mxmlc = str(pathlib.Path(flex_sdk) / 'bin' / ('mxmlc.exe' if os.name == 'nt' else 'mxmlc'))
    if not mxmlc:
        print('mxmlc not configured; skipping AS3 build')
        return
    root = pathlib.Path('as3/src/net/wg/app/impl/BattleVehicleMarkersApp.as')
    if not root.is_file():
        print('AS3 root not found; skipping AS3 build')
        return
    out = pathlib.Path('as3/bin/battleVehicleMarkersApp.swf')
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [mxmlc, '-source-path+=as3/src', '-static-link-runtime-shared-libraries=true', '-output=' + str(out), str(root)]
    print(' '.join(cmd))
    subprocess.check_call(cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--flash', action='store_true')
    parser.add_argument('--distribute', action='store_true')
    args = parser.parse_args()

    cfg = read_config()
    pyexe = cfg.get('software', {}).get('python') or sys.executable
    compile_python(pyexe)
    if args.flash:
        build_flash(cfg)

    temp = pathlib.Path('temp')
    build = pathlib.Path('build')
    if temp.exists():
        shutil.rmtree(str(temp))
    if build.exists():
        shutil.rmtree(str(build))
    temp.mkdir()
    build.mkdir()

    root = ET.Element('root')
    for key in ('id', 'version', 'name', 'description'):
        ET.SubElement(root, key).text = cfg['info'][key]
    meta = ET.tostring(root, encoding='utf-8')
    with open(str(temp / 'meta.xml'), 'wb') as fh:
        fh.write(meta)

    copytree('python', str(temp / 'res/scripts/client'), ignore=shutil.ignore_patterns('*.py'))
    copytree('resources/in', str(temp / 'res'))
    copytree('as3/bin', str(temp / 'res/gui/flash'))

    package = '%s_%s.wotmod' % (cfg['info']['id'], cfg['info']['version'])
    zip_dir(str(temp), str(build / package))
    print('created', build / package)

    if args.distribute:
        dist = temp / 'distribute' / 'mods' / cfg['game']['version']
        dist.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(build / package), str(dist / package))
        zip_dir(str(temp / 'distribute'), str(build / (package + '.zip')))


if __name__ == '__main__':
    main()

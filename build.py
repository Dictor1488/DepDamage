# -*- coding: utf-8 -*-
"""WoT .wotmod packer and standalone overlay SWF compiler for DepDamage."""

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


OVERLAY_SWF = pathlib.Path('as3/bin/DepDamageFlash.swf')
REQUIRED_PY_SOURCES = (
    pathlib.Path('python/gui/mods/mod_flyingdamage.py'),
    pathlib.Path('python/gui/mods/flyingdamage/__init__.py'),
    pathlib.Path('python/gui/mods/flyingdamage/hooks.py'),
    pathlib.Path('python/gui/mods/flyingdamage/overlay.py'),
)
REQUIRED_ARCHIVE_FILES = (
    'res/scripts/client/gui/mods/mod_flyingdamage.pyc',
    'res/scripts/client/gui/mods/flyingdamage/__init__.pyc',
    'res/scripts/client/gui/mods/flyingdamage/hooks.pyc',
    'res/scripts/client/gui/mods/flyingdamage/overlay.pyc',
    'res/gui/flash/DepDamageFlash.swf',
)


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
        if item.name in ignored or item.name == '.gitkeep':
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


def _clean_python_bytecode():
    python_root = pathlib.Path('python')
    if not python_root.is_dir():
        return
    for path in python_root.rglob('*.pyc'):
        path.unlink()
    for cache_dir in sorted(python_root.rglob('__pycache__'), reverse=True):
        shutil.rmtree(str(cache_dir))


def compile_python(pyexe):
    python_root = pathlib.Path('python')
    if not python_root.is_dir():
        raise RuntimeError('python source directory is missing')

    missing_sources = [str(path) for path in REQUIRED_PY_SOURCES if not path.is_file()]
    if missing_sources:
        raise RuntimeError('Required Python sources are missing: %s' % ', '.join(missing_sources))

    _clean_python_bytecode()

    try:
        version = subprocess.check_output(
            [pyexe, '-c', 'import sys; print(sys.version_info[0])']
        ).decode('ascii', 'replace').strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError('Python compiler is not available: %s' % exc)

    if version != '2':
        raise RuntimeError('WoT scripts must be compiled with Python 2.7, got major version %s from %s' % (version, pyexe))

    for path in sorted(python_root.rglob('*.py')):
        print('compile', path)
        subprocess.check_call([pyexe, '-m', 'py_compile', str(path)])

    missing_pyc = []
    for source in REQUIRED_PY_SOURCES:
        compiled = pathlib.Path(str(source) + 'c')
        if not compiled.is_file():
            missing_pyc.append(str(compiled))
    if missing_pyc:
        raise RuntimeError('Required Python bytecode was not generated: %s' % ', '.join(missing_pyc))


def _mxmlc_path(cfg):
    mxmlc = cfg.get('software', {}).get('mxmlc') or ''
    flex_sdk = cfg.get('software', {}).get('flex_sdk') or ''
    if mxmlc:
        return mxmlc
    if flex_sdk:
        return str(pathlib.Path(flex_sdk) / 'bin' / ('mxmlc.exe' if os.name == 'nt' else 'mxmlc'))
    return os.environ.get('MXMLC') or shutil.which('mxmlc')


def _as3_lib_args():
    libs_dir = pathlib.Path('as3/libs')
    if not libs_dir.is_dir():
        return []
    args = []
    for swc in sorted(libs_dir.rglob('*.swc')):
        swc_path = str(swc)
        if swc.name == 'playerglobal.swc':
            args.append('-library-path+=' + swc_path)
        else:
            args.append('-external-library-path+=' + swc_path)
    return args


def build_flash(cfg):
    mxmlc = _mxmlc_path(cfg)
    if not mxmlc:
        raise RuntimeError('mxmlc is not configured')

    if OVERLAY_SWF.exists():
        OVERLAY_SWF.unlink()
    OVERLAY_SWF.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        mxmlc,
        '-source-path+=as3/src',
        '-output=' + str(OVERLAY_SWF),
        '-target-player=32.0',
        '-swf-version=39',
        '-default-size=800,600',
        '-strict=true',
        '-optimize=true',
        '-warnings=true',
        '-static-link-runtime-shared-libraries=true',
    ]
    cmd.extend(_as3_lib_args())
    cmd.append('as3/src/com/flyingdamage/DepDamageFlash.as')
    print(' '.join(cmd))
    subprocess.check_call(cmd)

    if not OVERLAY_SWF.is_file() or OVERLAY_SWF.stat().st_size == 0:
        raise RuntimeError('DepDamageFlash.swf was not generated')


def _verify_package(package_path):
    with zipfile.ZipFile(str(package_path), 'r') as zf:
        names = set(zf.namelist())
        missing = [path for path in REQUIRED_ARCHIVE_FILES if path not in names]
        if missing:
            raise RuntimeError('Built .wotmod is incomplete; missing: %s' % ', '.join(missing))

        python_sources = sorted(name for name in names if name.endswith('.py'))
        if python_sources:
            raise RuntimeError('Built .wotmod unexpectedly contains Python sources: %s' % ', '.join(python_sources))

    print('verified package contents:')
    for path in REQUIRED_ARCHIVE_FILES:
        print('  ', path)


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

    if not OVERLAY_SWF.is_file():
        raise RuntimeError('Required SWF is missing: %s. Run build.py --flash first.' % OVERLAY_SWF)

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
    try:
        ET.indent(root, space='    ')
    except AttributeError:
        pass
    with open(str(temp / 'meta.xml'), 'wb') as fh:
        fh.write(ET.tostring(root, encoding='utf-8'))

    copytree('python', str(temp / 'res/scripts/client'), ignore=shutil.ignore_patterns('*.py', '__pycache__'))
    copytree('resources/in', str(temp / 'res'))
    copytree('as3/bin', str(temp / 'res/gui/flash'))

    package = '%s_%s.wotmod' % (cfg['info']['id'], cfg['info']['version'])
    package_path = build / package
    zip_dir(str(temp), str(package_path))
    _verify_package(package_path)
    print('created', package_path)

    if args.distribute:
        dist = temp / 'distribute' / 'mods' / cfg['game']['version']
        dist.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(package_path), str(dist / package))
        zip_dir(str(temp / 'distribute'), str(build / (package + '.zip')))


if __name__ == '__main__':
    main()

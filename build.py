# -*- coding: utf-8 -*-
"""WoT .wotmod packer and AS3 compiler for DepDamage."""

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


BROKEN_ROOT_SWF = pathlib.Path('as3/bin/battleVehicleMarkersApp.swf')
UI_SWF = pathlib.Path('as3/bin/depdamage_vehiclemarkers_ui.swf')
ORIGINAL_ROOT_SWF = pathlib.Path('resources/original/gui/flash/battleVehicleMarkersApp.swf')


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


def compile_python(pyexe):
    if not pathlib.Path('python').is_dir():
        return
    for path in pathlib.Path('python').rglob('*.py'):
        print('compile', path)
        try:
            subprocess.call([pyexe, '-m', 'py_compile', str(path)])
        except OSError:
            print('python compiler not available, keeping sources only:', path)


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


def _compile_swf(mxmlc, root, out):
    root = pathlib.Path(root)
    if not root.is_file():
        print('AS3 root not found; skipping', root)
        return False

    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        mxmlc,
        '-source-path+=as3/src',
        '-output=' + str(out),
        '-target-player=32.0',
        '-swf-version=39',
        '-strict=true',
        '-optimize=true',
        '-warnings=true',
        '-static-link-runtime-shared-libraries=true',
    ]
    cmd.extend(_as3_lib_args())
    cmd.append(str(root))

    print(' '.join(cmd))
    subprocess.check_call(cmd)
    return True


def _patch_original_root_swf(cfg):
    """Patch original WG root SWF if the caller supplied it.

    XVM does not rebuild battleVehicleMarkersApp.swf from AS3. It patches the
    original WG SWF so that it loads an external marker UI SWF into the current
    ApplicationDomain. We follow that same split:
    - depdamage_vehiclemarkers_ui.swf is compiled from our AS3 sources;
    - battleVehicleMarkersApp.swf is produced only by patching the original SWF.
    """
    if not ORIGINAL_ROOT_SWF.is_file():
        print('Original WG root SWF not found:', ORIGINAL_ROOT_SWF)
        print('Skipping patched battleVehicleMarkersApp.swf. This avoids packaging the broken self-built root SWF.')
        if BROKEN_ROOT_SWF.exists():
            BROKEN_ROOT_SWF.unlink()
        return False

    rabcdasm_dir = cfg.get('software', {}).get('rabcdasm_dir') or os.environ.get('RABCDASM_DIR', '')
    cmd = [
        sys.executable,
        'tools/patch_battle_vehicle_markers.py',
        '--original', str(ORIGINAL_ROOT_SWF),
        '--output', str(BROKEN_ROOT_SWF),
        '--ui-path', UI_SWF.name,
    ]
    if rabcdasm_dir:
        cmd.extend(['--rabcdasm-dir', rabcdasm_dir])
    print(' '.join(cmd))
    subprocess.check_call(cmd)
    return True


def build_flash(cfg):
    mxmlc = _mxmlc_path(cfg)
    if not mxmlc:
        print('mxmlc not configured; skipping AS3 build')
        return

    # Always clean old root SWF first. The old self-built root caused:
    # VerifyError #1001: The method RootApp is not implemented.
    if BROKEN_ROOT_SWF.exists():
        BROKEN_ROOT_SWF.unlink()

    # Build only the external marker UI SWF. This is the SWF that should be
    # loaded by the patched original battleVehicleMarkersApp.swf.
    _compile_swf(
        mxmlc,
        'as3/src/com/flyingdamage/DepDamageVehicleMarkersMod.as',
        str(UI_SWF)
    )

    # Produce battleVehicleMarkersApp.swf only from the original WG SWF + patch.
    _patch_original_root_swf(cfg)


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
    try:
        ET.indent(root, space='    ')
    except AttributeError:
        pass
    meta = ET.tostring(root, encoding='utf-8')
    with open(str(temp / 'meta.xml'), 'wb') as fh:
        fh.write(meta)

    if any(pathlib.Path('python').rglob('*.pyc')):
        copytree('python', str(temp / 'res/scripts/client'), ignore=shutil.ignore_patterns('*.py'))
    else:
        copytree('python', str(temp / 'res/scripts/client'))

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

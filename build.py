# SPDX-License-Identifier: MIT
# Copyright (c) 2015-2025 Andrii Andrushchyshyn
"""
Build script for creating and packaging World of Tanks modifications.

Current project mode:
- Python entry point is only a lightweight mod marker.
- Full AS3 source for vehicle markers is built into battleVehicleMarkersApp.swf.
- No old Gameface files, no prebuilt old SWF, no FlyingDamageApp overlay path.
"""

import argparse
import datetime
import json
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Dict, List, Optional, Set

try:
    import psutil
except ImportError:
    raise ImportError("psutil is not installed. Please run 'pip install psutil' to install it.")


class ElapsedFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__()
        self.start_time = time.time()

    def format(self, record: logging.LogRecord) -> str:
        elapsed_seconds = record.created - self.start_time
        elapsed = datetime.timedelta(seconds=elapsed_seconds)
        return f"{elapsed.seconds:03d}.{int(elapsed.microseconds / 1000):03d} {record.getMessage()}"


def setup_logger() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(ElapsedFormatter())
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger


class AppConfig:
    class Software:
        def __init__(self, data: Dict[str, Any]) -> None:
            self.animate: Optional[str] = data.get('animate')
            self.python: Optional[str] = data.get('python')
            self.mxmlc: Optional[str] = data.get('mxmlc')
            self.flex_sdk: Optional[str] = data.get('flex_sdk')

    class Game:
        def __init__(self, data: Dict[str, Any]) -> None:
            self.force: bool = data.get('force', False)
            self.folder: Optional[str] = data.get('folder')
            self.version: Optional[str] = data.get('version')

    class Info:
        def __init__(self, data: Dict[str, Any]) -> None:
            self.id: Optional[str] = data.get('id')
            self.name: Optional[str] = data.get('name')
            self.description: Optional[str] = data.get('description')
            self.version: Optional[str] = data.get('version')

    def __init__(self, data: Dict[str, Any]) -> None:
        self.version: int = data.get('version', 0)
        self.software = self.Software(data.get('software', {}))
        self.game = self.Game(data.get('game', {}))
        self.info = self.Info(data.get('info', {}))


def copytree(source: str, destination: str, ignore: Optional[callable] = None) -> None:
    source_path = pathlib.Path(source)
    dest_path = pathlib.Path(destination)
    dest_path.mkdir(parents=True, exist_ok=True)

    names = os.listdir(source_path)
    ignored_names: Set[str] = ignore(str(source_path), names) if ignore else set()

    for name in names:
        if name in ignored_names or '.gitkeep' in name:
            continue
        srcname = source_path / name
        dstname = dest_path / name
        try:
            if srcname.is_dir():
                copytree(str(srcname), str(dstname), ignore)
            else:
                shutil.copy2(str(srcname), str(dstname))
        except (IOError, os.error) as why:
            logger.error("Can't copy %s to %s: %s", srcname, dstname, str(why))


def zip_folder(source: str, destination: str, mode: str = 'w', compression: int = zipfile.ZIP_STORED) -> None:
    source_path = pathlib.Path(source)
    with zipfile.ZipFile(destination, mode, compression) as zipfh:
        now = tuple(datetime.datetime.now().timetuple())[:6]
        for file_path in source_path.rglob('*'):
            arcname = file_path.relative_to(source_path)
            if file_path.is_dir():
                info = zipfile.ZipInfo(str(arcname).replace('\\', '/') + '/', now)
                info.compress_type = compression
                zipfh.writestr(info, '')
            else:
                info = zipfile.ZipInfo(str(arcname).replace('\\', '/'), now)
                info.external_attr = 33206 << 16
                info.compress_type = compression
                zipfh.writestr(info, file_path.read_bytes())


def _mxmlc_path(config: AppConfig) -> Optional[str]:
    if config.software.mxmlc:
        return config.software.mxmlc
    if config.software.flex_sdk:
        sdk = pathlib.Path(config.software.flex_sdk)
        exe = sdk / 'bin' / ('mxmlc.exe' if os.name == 'nt' else 'mxmlc')
        return str(exe)
    env = os.environ.get('MXMLC')
    if env:
        return env
    sdk = os.environ.get('FLEX_HOME') or os.environ.get('FLEX_SDK')
    if sdk:
        exe = pathlib.Path(sdk) / 'bin' / ('mxmlc.exe' if os.name == 'nt' else 'mxmlc')
        return str(exe)
    return shutil.which('mxmlc')


def build_as3_vehicle_markers(config: AppConfig, args: argparse.Namespace) -> None:
    src_root = pathlib.Path('as3/src_flash/src')
    app_file = src_root / 'net/wg/app/impl/BattleVehicleMarkersApp.as'
    if not app_file.is_file():
        logger.info('No AS3 marker root found: %s', app_file)
        return

    output = pathlib.Path('as3/bin/battleVehicleMarkersApp.swf')
    output.parent.mkdir(parents=True, exist_ok=True)

    mxmlc = _mxmlc_path(config)
    if not mxmlc:
        raise FileNotFoundError('mxmlc not configured. Set build.json software.mxmlc, software.flex_sdk, MXMLC, FLEX_HOME, or add mxmlc to PATH.')

    cmd = [
        mxmlc,
        '-source-path+=as3/src_flash/src',
        '-output=' + str(output),
        '-static-link-runtime-shared-libraries=true',
        str(app_file),
    ]
    logger.info('Building AS3 marker SWF: %s', output)
    logger.info('mxmlc root class: %s', app_file)
    logger.info('mxmlc command: %s', ' '.join(cmd))
    subprocess.check_call(cmd)
    logger.info('AS3 marker SWF built: %s', output)


def build_python(config: AppConfig) -> None:
    python_source_dir = pathlib.Path('python')
    if not python_source_dir.is_dir():
        return
    if not config.software.python:
        raise ValueError('Python executable path is not configured in build.json')

    for file_path in python_source_dir.rglob('*.py'):
        try:
            subprocess.check_output(
                [config.software.python, '-m', 'py_compile', str(file_path)],
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8'
            )
            logger.info('Python compiled: %s', file_path)
        except subprocess.CalledProcessError as e:
            logger.error('Python fail compile: %s\n%s', file_path, e.output)


def main() -> None:
    parser = argparse.ArgumentParser(description='Build script for WoT mods.')
    parser.add_argument('--flash', action='store_true', help='Build AS3 marker SWF with mxmlc.')
    parser.add_argument('--ingame', action='store_true', help='Copy the build into the game directory.')
    parser.add_argument('--distribute', action='store_true', help='Create a distributable archive.')
    parser.add_argument('--run', action='store_true', help='Run the game after a successful build.')
    args = parser.parse_args()

    config_path = pathlib.Path('build.json')
    if not config_path.is_file():
        raise FileNotFoundError('Config not found: build.json')

    with config_path.open('r', encoding='utf-8') as fh:
        config = AppConfig(json.load(fh))

    if config.game.force:
        game_folder = pathlib.Path(config.game.folder) if config.game.folder else None
        game_version = config.game.version
    else:
        game_folder = pathlib.Path(os.environ.get('WOT_FOLDER', config.game.folder or ''))
        game_version = os.environ.get('WOT_VERSION', config.game.version or '')

    if not game_folder or not game_version:
        raise ValueError('Game folder or version is not configured.')

    temp_dir = pathlib.Path('temp')
    build_dir = pathlib.Path('build')
    if temp_dir.is_dir():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    if build_dir.is_dir():
        shutil.rmtree(build_dir)
    build_dir.mkdir()

    logger.info('Starting build process...')
    build_python(config)
    if args.flash:
        build_as3_vehicle_markers(config, args)

    logger.info('Packaging mod...')
    package_name = f'{config.info.id}_{config.info.version}.wotmod'

    root = ET.Element('root')
    ET.SubElement(root, 'id').text = config.info.id
    ET.SubElement(root, 'version').text = config.info.version
    ET.SubElement(root, 'name').text = config.info.name
    ET.SubElement(root, 'description').text = config.info.description
    ET.indent(root, space='    ')
    meta_content = ET.tostring(root, encoding='unicode')

    if pathlib.Path('resources/in').is_dir():
        copytree('resources/in', str(temp_dir / 'res'))
    if pathlib.Path('as3/bin').is_dir():
        copytree('as3/bin', str(temp_dir / 'res/gui/flash'))
    if pathlib.Path('python').is_dir():
        copytree('python', str(temp_dir / 'res/scripts/client'), ignore=shutil.ignore_patterns('*.py'))
    (temp_dir / 'meta.xml').write_text(meta_content, encoding='utf-8')

    zip_folder(str(temp_dir), str(build_dir / package_name))
    logger.info('Package created: %s', build_dir / package_name)

    wot_packages_dir = game_folder / 'mods' / game_version
    if args.ingame:
        if not wot_packages_dir.is_dir():
            raise FileNotFoundError(f'WoT mods folder not found: {wot_packages_dir}')
        exe_name = 'worldoftanks.exe'
        for proc in psutil.process_iter(['name', 'pid']):
            name = (proc.info.get('name') or '').lower()
            if exe_name in name:
                try:
                    p = psutil.Process(proc.info['pid'])
                    p.terminate()
                    logger.info('WoT client closing (pid: %s)', proc.info['pid'])
                    p.wait(timeout=10)
                except psutil.Error as e:
                    logger.warning('Could not terminate WoT client (pid: %s): %s', proc.info['pid'], e)
        logger.info('Copying package to: %s', wot_packages_dir / package_name)
        shutil.copy2(str(build_dir / package_name), str(wot_packages_dir))

    if args.distribute:
        logger.info('Creating distribution archive...')
        dist_dir = temp_dir / 'distribute'
        dist_mods_dir = dist_dir / 'mods' / game_version
        dist_mods_dir.mkdir(parents=True)
        shutil.copy2(str(build_dir / package_name), str(dist_mods_dir))
        if pathlib.Path('resources/out').is_dir():
            copytree('resources/out', str(dist_dir))
        zip_name = f'{config.info.id}_{config.info.version}.zip'
        zip_folder(str(dist_dir), str(build_dir / zip_name))
        logger.info('Distribution archive created: %s', build_dir / zip_name)

    logger.info('Cleaning up temporary files...')
    cleanup_paths: List[pathlib.Path] = [
        temp_dir,
        pathlib.Path('EvalScript error.tmp'),
        pathlib.Path('as3/DataStore')
    ]
    cleanup_paths.extend(pathlib.Path('python').rglob('*.pyc'))
    for path in cleanup_paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            path.unlink(missing_ok=True)

    if args.run:
        executable_path = game_folder / 'worldoftanks.exe'
        if executable_path.is_file():
            logger.info('Starting World of Tanks client...')
            subprocess.Popen([str(executable_path)])
        else:
            logger.warning('Could not find game executable to run at: %s', executable_path)

    logger.info('Build finished successfully.')


if __name__ == '__main__':
    logger = setup_logger()
    try:
        main()
    except Exception as e:
        logger.exception('An unhandled error occurred: %s', e)
        sys.exit(1)

# -*- coding: utf-8 -*-
"""Patch original WG battleVehicleMarkersApp.swf to load DepDamage marker UI SWF.

This follows the same high-level flow as XVM:
- disassemble original WG battleVehicleMarkersApp.swf with RABCDAsm tools;
- patch BattleVehicleMarkersApp.class.asasm;
- reassemble the ABC;
- replace ABC 0 in a copy of the original SWF.

Required external tools from RABCDAsm must be available in PATH or passed with --rabcdasm-dir:
- abcexport[.exe]
- rabcdasm[.exe]
- rabcasm[.exe]
- abcreplace[.exe]
"""

from __future__ import print_function

import argparse
import os
import pathlib
import shutil
import subprocess
import sys


ON_LIBS_OLD = '''      findpropstrict      QName(ProtectedNamespace("net.wg.app.iml.base:RootApp"), "callRegisterCallback")
      callpropvoid        QName(ProtectedNamespace("net.wg.app.iml.base:RootApp"), "callRegisterCallback"), 0'''


def depdamage_loader_code(ui_path):
    return '''      getlocal0
      pushstring          "%s"
      callpropvoid        QName(PackageNamespace(""), "loadDepDamage"), 1''' % ui_path


DEP_TRAITS = '''  end ; trait
  trait slot QName(PackageNamespace(""), "depdamage_vm_swf") type QName(PackageNamespace("flash.display"), "DisplayObject") value Null() end
  trait method QName(PackageNamespace(""), "loadDepDamage")
   method
    name "loadDepDamage"
    refid "net.wg.app.impl:BattleVehicleMarkersApp/instance/loadDepDamage"
    param QName(PackageNamespace(""), "String")
    returns QName(PackageNamespace(""), "void")
    flag HAS_PARAM_NAMES
    paramname "swfPath"
    body
     maxstack 5
     localcount 3
     initscopedepth 0
     maxscopedepth 1
     code
      getlocal0
      pushscope

      findpropstrict      QName(PackageNamespace("flash.display"), "Loader")
      constructprop       QName(PackageNamespace("flash.display"), "Loader"), 0
      coerce              QName(PackageNamespace("flash.display"), "Loader")
      setlocal2

      findpropstrict      QName(PackageNamespace(""), "addChild")
      getlocal2
      callpropvoid        QName(PackageNamespace(""), "addChild"), 1

      getlocal2
      getproperty         QName(PackageNamespace(""), "contentLoaderInfo")
      pushstring          "complete"
      getlocal0
      getproperty         QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedComplete")
      callpropvoid        QName(PackageNamespace(""), "addEventListener"), 2

      getlocal2
      getproperty         QName(PackageNamespace(""), "contentLoaderInfo")
      pushstring          "ioError"
      getlocal0
      getproperty         QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedError")
      callpropvoid        QName(PackageNamespace(""), "addEventListener"), 2

      getlocal2
      findpropstrict      QName(PackageNamespace("flash.net"), "URLRequest")
      getlocal1
      constructprop       QName(PackageNamespace("flash.net"), "URLRequest"), 1
      findpropstrict      QName(PackageNamespace("flash.system"), "LoaderContext")
      pushfalse
      getlex              QName(PackageNamespace("flash.system"), "ApplicationDomain")
      getproperty         QName(PackageNamespace(""), "currentDomain")
      constructprop       QName(PackageNamespace("flash.system"), "LoaderContext"), 2
      callpropvoid        QName(PackageNamespace(""), "load"), 2

      returnvoid
     end ; code
    end ; body
   end ; method
  end ; trait
  trait method QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedComplete")
   method
    name "onDepDamageSWFLoadedComplete"
    refid "net.wg.app.impl:BattleVehicleMarkersApp/instance/net.wg.app.impl:BattleVehicleMarkersApp/onDepDamageSWFLoadedComplete"
    param QName(PackageNamespace("flash.events"), "Event")
    returns QName(PackageNamespace(""), "void")
    flag HAS_PARAM_NAMES
    paramname "e"
    body
     maxstack 2
     localcount 3
     initscopedepth 0
     maxscopedepth 1
     code
      getlocal0
      pushscope

      getlocal1
      getproperty         QName(PackageNamespace(""), "currentTarget")
      getlex              QName(PackageNamespace("flash.display"), "LoaderInfo")
      astypelate
      coerce              QName(PackageNamespace("flash.display"), "LoaderInfo")
      setlocal2

      getlocal0
      getlocal2
      getproperty         QName(PackageNamespace(""), "content")
      setproperty         QName(PackageNamespace(""), "depdamage_vm_swf")

      findpropstrict      QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedFinish")
      getlocal2
      callpropvoid        QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedFinish"), 1

      returnvoid
     end ; code
    end ; body
   end ; method
  end ; trait
  trait method QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedError")
   method
    name "onDepDamageSWFLoadedError"
    refid "net.wg.app.impl:BattleVehicleMarkersApp/instance/net.wg.app.impl:BattleVehicleMarkersApp/onDepDamageSWFLoadedError"
    param QName(PackageNamespace("flash.events"), "IOErrorEvent")
    returns QName(PackageNamespace(""), "void")
    flag HAS_PARAM_NAMES
    paramname "e"
    body
     maxstack 3
     localcount 2
     initscopedepth 0
     maxscopedepth 1
     code
      getlocal0
      pushscope

      findpropstrict      QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedFinish")
      getlocal1
      getproperty         QName(PackageNamespace(""), "currentTarget")
      getlex              QName(PackageNamespace("flash.display"), "LoaderInfo")
      astypelate
      callpropvoid        QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedFinish"), 1

      returnvoid
     end ; code
    end ; body
   end ; method
  end ; trait
  trait method QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedFinish")
   method
    name "onDepDamageSWFLoadedFinish"
    refid "net.wg.app.impl:BattleVehicleMarkersApp/instance/net.wg.app.impl:BattleVehicleMarkersApp/onDepDamageSWFLoadedFinish"
    param QName(PackageNamespace("flash.display"), "LoaderInfo")
    returns QName(PackageNamespace(""), "void")
    flag HAS_PARAM_NAMES
    paramname "loaderInfo"
    body
     maxstack 3
     localcount 2
     initscopedepth 0
     maxscopedepth 1
     code
      getlocal0
      pushscope

      getlocal1
      pushstring          "complete"
      getlocal0
      getproperty         QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedComplete")
      callpropvoid        QName(PackageNamespace(""), "removeEventListener"), 2

      getlocal1
      pushstring          "ioError"
      getlocal0
      getproperty         QName(PrivateNamespace("net.wg.app.impl:BattleVehicleMarkersApp"), "onDepDamageSWFLoadedError")
      callpropvoid        QName(PackageNamespace(""), "removeEventListener"), 2

      findpropstrict      QName(ProtectedNamespace("net.wg.app.iml.base:RootApp"), "callRegisterCallback")
      callpropvoid        QName(ProtectedNamespace("net.wg.app.iml.base:RootApp"), "callRegisterCallback"), 0

      returnvoid
     end ; code
    end ; body
   end ; method'''


def exe_name(name):
    return name + ('.exe' if os.name == 'nt' else '')


def resolve_tool(name, tool_dir):
    candidate = pathlib.Path(tool_dir) / exe_name(name) if tool_dir else None
    if candidate and candidate.is_file():
        return str(candidate)
    found = shutil.which(exe_name(name)) or shutil.which(name)
    if found:
        return found
    raise RuntimeError('Required RABCDAsm tool not found: %s' % name)


def run(cmd, cwd=None):
    print(' '.join(str(x) for x in cmd))
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def patch_asasm(path, ui_path):
    text = path.read_text(encoding='utf-8')
    if 'loadDepDamage' in text:
        print('Already patched:', path)
        return

    # XVM changes only the onLibsLoadingComplete body maxstack from 1 to 2.
    marker = 'refid "net.wg.app.impl:BattleVehicleMarkersApp/instance/net.wg.app.impl:BattleVehicleMarkersApp:onLibsLoadingComplete"'
    idx = text.find(marker)
    if idx < 0:
        raise RuntimeError('onLibsLoadingComplete refid not found in %s' % path)
    maxstack_idx = text.find('     maxstack 1', idx)
    if maxstack_idx < 0:
        raise RuntimeError('Expected maxstack 1 not found near onLibsLoadingComplete in %s' % path)
    text = text[:maxstack_idx] + text[maxstack_idx:].replace('     maxstack 1', '     maxstack 2', 1)

    if ON_LIBS_OLD not in text:
        raise RuntimeError('callRegisterCallback block not found in %s' % path)
    text = text.replace(ON_LIBS_OLD, depdamage_loader_code(ui_path), 1)

    insert_before = '  end ; trait\n  end ; instance\n  cinit'
    if insert_before not in text:
        raise RuntimeError('Trait insertion point not found in %s' % path)
    text = text.replace(insert_before, DEP_TRAITS + '\n  end ; trait\n  end ; instance\n  cinit', 1)
    path.write_text(text, encoding='utf-8')
    print('Patched ASASM:', path)


def find_single(pattern, root):
    matches = list(pathlib.Path(root).glob(pattern))
    if not matches:
        raise RuntimeError('No match for %s in %s' % (pattern, root))
    if len(matches) > 1:
        print('Warning: multiple matches for %s, using %s' % (pattern, matches[0]))
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', required=True, help='Original WG battleVehicleMarkersApp.swf')
    parser.add_argument('--output', required=True, help='Patched battleVehicleMarkersApp.swf output')
    parser.add_argument('--ui-path', default='depdamage_vehiclemarkers_ui.swf', help='Runtime path loaded by patched root SWF')
    parser.add_argument('--rabcdasm-dir', default=os.environ.get('RABCDASM_DIR', ''), help='Directory with RABCDAsm tools')
    parser.add_argument('--work-dir', default='temp/patch_battleVehicleMarkersApp')
    args = parser.parse_args()

    original = pathlib.Path(args.original)
    output = pathlib.Path(args.output)
    work = pathlib.Path(args.work_dir)
    if not original.is_file():
        raise RuntimeError('Original SWF not found: %s' % original)

    abcexport = resolve_tool('abcexport', args.rabcdasm_dir)
    rabcdasm = resolve_tool('rabcdasm', args.rabcdasm_dir)
    rabcasm = resolve_tool('rabcasm', args.rabcdasm_dir)
    abcreplace = resolve_tool('abcreplace', args.rabcdasm_dir)

    if work.exists():
        shutil.rmtree(str(work))
    work.mkdir(parents=True)

    swf_copy = work / 'battleVehicleMarkersApp.swf'
    shutil.copy2(str(original), str(swf_copy))

    run([abcexport, str(swf_copy)], cwd=work)
    abc = find_single('battleVehicleMarkersApp-*.abc', work)
    run([rabcdasm, str(abc)], cwd=work)

    disasm_dir = work / abc.stem
    class_asasm = disasm_dir / 'net/wg/app/impl/BattleVehicleMarkersApp.class.asasm'
    if not class_asasm.is_file():
        raise RuntimeError('BattleVehicleMarkersApp.class.asasm not found after disassembly')
    patch_asasm(class_asasm, args.ui_path)

    main_asasm = find_single('*.main.asasm', disasm_dir)
    run([rabcasm, str(main_asasm)], cwd=disasm_dir)

    patched_abc = disasm_dir / (main_asasm.stem.replace('.main', '') + '.abc')
    if not patched_abc.is_file():
        # Common rabcasm output: same base name as *.main.asasm without .main.asasm
        patched_abc = disasm_dir / (abc.stem + '.abc')
    if not patched_abc.is_file():
        raise RuntimeError('Patched ABC not found after rabcasm')

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(swf_copy), str(output))
    run([abcreplace, str(output), '0', str(patched_abc)], cwd=work)
    print('Patched SWF written:', output)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)

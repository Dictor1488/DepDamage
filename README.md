# Flying Damage

WoT mod that shows floating damage numbers through a Scaleform/SWF battle view.

## Version 3.3.0

This version adds two positioning modes:

- `World anchor / XVM-like` is the default. The mod captures a fixed world-space point above the damaged vehicle at hit time. The SWF re-projects that point every frame while the number rises, so the damage behaves like it belongs to the world/vehicle position instead of a free fullscreen overlay.
- `Screen fixed fallback` freezes the starting screen x/y and animates upward in pixels. Use it only if world projection behaves incorrectly on a specific client build.

## Main files

```text
python/gui/mods/mod_flyingdamage.py
python/gui/mods/flyingdamage/hooks.py
python/gui/mods/flyingdamage/__init__.py
python/gui/mods/flyingdamage/settings/config.py
as3/src_flash/src/com/flyingdamage/FlyingDamageApp.as
as3/src_flash/src/com/flyingdamage/DamageLayer.as
as3/src_flash/src/com/flyingdamage/FloatingNumber.as
build.py
build.json
```

## Build SWF

```text
mxmlc -source-path+=as3/src_flash/src ^
  -library-path+=as3/libs/playerglobal.swc ^
  -external-library-path+=as3/libs/common-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/common_i18n_library-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/base_app-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/gui_base-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/gui_lobby-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/gui_battle-1.0-SNAPSHOT.swc ^
  -external-library-path+=as3/libs/lobby.swc ^
  -external-library-path+=as3/libs/battle.swc ^
  -target-player=32.0 -swf-version=39 -optimize=true ^
  -output=as3/bin/FlyingDamageApp.swf ^
  -- as3/src_flash/src/com/flyingdamage/FlyingDamageApp.as
```

Then copy:

```text
as3/bin/FlyingDamageApp.swf -> resources/in/gui/flash/FlyingDamageApp.swf
```

## Build wotmod

```text
pip install psutil
python build.py --distribute
```

Expected package name:

```text
build/com.author.flyingdamage_3.3.0.wotmod
```

## Notes

The source code is ready. The SWF still needs to be compiled with Flex/mxmlc or the existing CI workflow before packaging the final `.wotmod`.

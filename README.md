# DepDamage

Standalone World of Tanks floating-damage overlay.

## Architecture

DepDamage does not replace or patch `battleVehicleMarkersApp.swf` and does not replace the stock `VehicleMarker` class.

Flow:

1. Hook `VehicleMarkerPlugin.start`, `stop`, and `_updateVehicleHealth`.
2. Create a separate transparent `ExternalFlashComponent` named `DepDamageFlash.swf`.
3. On damage, use the stock `VehicleMarker.fetchMatrixProvider(vehicle)` position.
4. Project that 3D marker point through the current camera view-projection matrix.
5. Convert normalized coordinates to exact screen pixels.
6. Create the damage number once at that screen position.
7. Animate only its local Y/alpha afterward, so later camera movement does not drag it.

The overlay uses `NO_SCALE`, an 800x600 SWF stage, and shifts its AS3 root to the real screen top-left. This keeps one SWF pixel equal to one screen pixel.

## Main files

```text
python/gui/mods/mod_flyingdamage.py
python/gui/mods/flyingdamage/hooks.py
python/gui/mods/flyingdamage/overlay.py
as3/src/com/flyingdamage/DepDamageFlash.as
as3/src/com/flyingdamage/FloatingDamageLayer.as
as3/src/com/flyingdamage/FloatingDamageNumber.as
as3/src/com/flyingdamage/FlyingDamageConfig.as
.github/workflows/release.yml
build.py
build.json
```

## Build

```bash
python build.py --flash --distribute
```

The build produces:

```text
as3/bin/DepDamageFlash.swf
build/com.author.depdmg_<version>.wotmod
```

No original WG SWF and no RABCDAsm tools are required.

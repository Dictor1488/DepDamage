# DepDamage

Clean rebuild of a World of Tanks flying damage mod.

## Goal

Implement XVM-style floating damage:

1. Python hooks vehicle marker creation and vehicle health updates.
2. The stock vehicle marker symbol is replaced with `DepDamageVehicleMarker`.
3. Damage data is packed into `updateHealth(newHealth, damageFlag, damageType)`.
4. AS3 unpacks the data, calculates `damageDelta`, creates a text field inside the marker, moves it upward, fades it out, merges rapid hits from the same attacker within 400 ms, and removes the clip.

## Current state

Connected XVM-like implementation scaffold:

```text
python/gui/mods/mod_flyingdamage.py
python/gui/mods/flyingdamage/hooks.py
python/gui/mods/flyingdamage/consts.py
as3/src/com/flyingdamage/FlyingDamageConfig.as
as3/src/com/flyingdamage/FloatingDamageLayer.as
as3/src/com/flyingdamage/FloatingDamageNumber.as
as3/src/com/flyingdamage/DepDamageVehicleMarkersMod.as
as3/src/net/wg/gui/battle/views/vehicleMarkers/DepDamageVehicleMarker.as
as3/libs/*.swc
patches/depdamage_battleVehicleMarkersApp.vma.patch
tools/patch_battle_vehicle_markers.py
.github/workflows/release.yml
build.py
build.json
```

## XVM-style SWF loading flow

Do **not** rebuild `battleVehicleMarkersApp.swf` from AS3 source. That produced `VerifyError #1001: The method RootApp is not implemented` in WoT.

XVM keeps the original WG/Lesta `battleVehicleMarkersApp.swf` and patches its bytecode. DepDamage now follows the same design:

1. Compile only the external marker UI SWF:

```text
as3/bin/depdamage_vehiclemarkers_ui.swf
```

2. Patch the original WG root SWF so it loads `depdamage_vehiclemarkers_ui.swf` into `ApplicationDomain.currentDomain` before calling `callRegisterCallback()`.

3. Python replaces the marker symbol:

```text
VehicleMarker -> DepDamageVehicleMarker
```

4. Because the external UI SWF is loaded into the current application domain, the game can resolve `DepDamageVehicleMarker`.

## Original WG SWF requirement

To produce a working patched root SWF, put the original game file here:

```text
resources/original/gui/flash/battleVehicleMarkersApp.swf
```

The build will then create:

```text
as3/bin/battleVehicleMarkersApp.swf
```

If the original WG SWF is missing, the build intentionally skips `battleVehicleMarkersApp.swf` so a broken self-built root SWF is not packaged.

## RABCDAsm requirement

The patcher needs RABCDAsm tools:

```text
abcexport
rabcdasm
rabcasm
abcreplace
```

Set either:

```text
RABCDASM_DIR=C:\path\to\rabcdasm
```

or add the tools to `PATH`.

You can also add this to `build.json`:

```json
{
  "software": {
    "rabcdasm_dir": "C:/path/to/rabcdasm"
  }
}
```

## Imported from REductionTimer

The full known SWC pack was copied into `as3/libs`:

```text
playerglobal.swc
common-1.0-SNAPSHOT.swc
common_i18n_library-1.0-SNAPSHOT.swc
base_app-1.0-SNAPSHOT.swc
gui_base-1.0-SNAPSHOT.swc
gui_lobby-1.0-SNAPSHOT.swc
gui_battle-1.0-SNAPSHOT.swc
lobby.swc
battle.swc
```

## Build and release

Use GitHub Actions: `.github/workflows/release.yml`.

Manual build:

```bash
python build.py --flash --distribute
```

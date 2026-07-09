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
as3/src/net/wg/gui/battle/views/vehicleMarkers/DepDamageVehicleMarker.as
as3/src/net/wg/app/impl/BattleVehicleMarkersApp.as
as3/libs/*.swc
.github/workflows/release.yml
build.py
build.json
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

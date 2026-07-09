# DepDamage

Clean rebuild of a World of Tanks flying damage mod.

## Goal

Implement XVM-style floating damage:

1. Python hooks vehicle marker creation and vehicle health updates.
2. The stock vehicle marker symbol is replaced with `DepDamageVehicleMarker`.
3. Damage data is packed into `updateHealth(newHealth, damageFlag, damageType)`.
4. AS3 unpacks the data, calculates `damageDelta`, creates a text field inside the marker, moves it upward, fades it out, and removes it.

This is intentionally rebuilt from zero. Old broken overlay/Gameface experiments were removed.

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
.github/workflows/build.yml
build.py
build.json
```

## Build

```bash
python build.py --flash --distribute
```

If `mxmlc` is not configured, the Python/package part can still be packed, but the final SWF will not be rebuilt.

## Release

The repository includes a GitHub Actions build workflow. Push a tag like `v0.1.0` or run the workflow manually. Existing GitHub Releases are kept separately in the Releases section.

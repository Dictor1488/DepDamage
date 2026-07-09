# DepDamage

Clean rebuild of a World of Tanks flying damage mod.

## Goal

Implement XVM-style floating damage:

1. Python hooks vehicle health updates.
2. Damage data is passed to the vehicle marker.
3. AS3 creates a text field inside the marker layer.
4. The number rises upward, fades out, then removes itself.

This is intentionally rebuilt from zero. Old broken overlay/Gameface experiments were removed.

## Current state

Initial XVM-like project scaffold:

```text
python/gui/mods/mod_flyingdamage.py
python/gui/mods/flyingdamage/hooks.py
python/gui/mods/flyingdamage/consts.py
as3/src/com/flyingdamage/FloatingDamageLayer.as
as3/src/com/flyingdamage/FloatingDamageNumber.as
as3/src/com/flyingdamage/FlyingDamageConfig.as
as3/src/net/wg/app/impl/BattleVehicleMarkersApp.as
build.py
build.json
```

## Notes

Releases are kept in GitHub Releases. The repository source is now the new clean workspace.

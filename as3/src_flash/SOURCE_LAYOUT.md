# Battle vehicle markers AS3 source

This directory is for AS3 source of `battleVehicleMarkersApp.swf`.

Expected layout after extracting the provided source archive:

```text
as3/src_flash/src/App.as
as3/src_flash/src/net/wg/app/impl/BattleVehicleMarkersApp.as
as3/src_flash/src/net/wg/gui/battle/views/vehicleMarkers/VehicleMarker.as
as3/src_flash/src/net/wg/gui/battle/views/vehicleMarkers/DamageLabel.as
as3/src_flash/src/net/wg/gui/battle/views/vehicleMarkers/DamageAnimatedLabel.as
as3/src_flash/src/com/greensock/...
```

Build output:

```text
as3/bin/battleVehicleMarkersApp.swf
```

The package step copies `as3/bin` into the `.wotmod` as:

```text
res/gui/flash/battleVehicleMarkersApp.swf
```

Do not commit old Gameface files, old binary SWF replacements, or the previous `FlyingDamageApp` overlay renderer.

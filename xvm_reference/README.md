# XVM vehicle marker SWF patch reference

This folder keeps the reference patch copied from XVM for studying the correct vehicle-marker loading flow.

Source:
- Repository: `modxvm/XVM`
- Commit: `ba84d9faf643ebee951adb94c97c35cf48631d36`
- Original path: `src/xvm_actionscript/swf_wg/battleVehicleMarkersApp.vma.patch`

Important idea from XVM:

1. Do not rebuild `battleVehicleMarkersApp.swf` from AS3 source.
2. Patch the original WG/Lesta `battleVehicleMarkersApp.swf` bytecode.
3. Replace the direct `callRegisterCallback()` in `onLibsLoadingComplete()` with a loader call.
4. Load an external marker UI SWF into `ApplicationDomain.currentDomain`.
5. Call `callRegisterCallback()` only after the external SWF is loaded or after an IO error fallback.

For DepDamage, the XVM path:

```text
../../mods/openwg_packages/xvm_battle/as_battle/xvm_vehiclemarkers_ui.swf
```

needs to become a DepDamage path, for example:

```text
depdamage_vehiclemarkers_ui.swf
```

or another path that works from `gui/flash/battleVehicleMarkersApp.swf` at runtime.

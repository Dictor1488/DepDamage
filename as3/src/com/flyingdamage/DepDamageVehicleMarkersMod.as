package com.flyingdamage
{
    import flash.display.Sprite;
    import net.wg.gui.battle.views.vehicleMarkers.DepDamageVehicleMarker;

    /**
     * External marker UI SWF, loaded by BattleVehicleMarkersApp like XVM loads
     * xvm_vehiclemarkers_ui.swf. The class reference forces the linker to export
     * DepDamageVehicleMarker into the current ApplicationDomain.
     */
    public class DepDamageVehicleMarkersMod extends Sprite
    {
        private static const MARKER_CLASS:Class = DepDamageVehicleMarker;

        public function DepDamageVehicleMarkersMod()
        {
            super();
        }
    }
}

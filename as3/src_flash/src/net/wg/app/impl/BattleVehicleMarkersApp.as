package net.wg.app.impl
{
    import net.wg.gui.battle.views.vehicleMarkers.VehicleMarkersManager;

    /**
     * Minimal root for battleVehicleMarkersApp.swf.
     * The old FlyingDamageApp overlay is not used.
     */
    public class BattleVehicleMarkersApp extends VehicleMarkersManager
    {
        public function BattleVehicleMarkersApp()
        {
            super();
        }

        public function get vehicleMarkersCanvas() : VehicleMarkersManager
        {
            return this;
        }
    }
}

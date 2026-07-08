package net.wg.gui.battle.views.vehicleMarkers
{
    import flash.display.Sprite;
    import flash.utils.Dictionary;

    /**
     * Compact manager shell for the simplified marker build.
     * It keeps only marker storage and forwards health/damage calls to VehicleMarker.
     */
    public class VehicleMarkersManager extends Sprite
    {
        private static var _instance:VehicleMarkersManager;

        private var markers:Dictionary = new Dictionary();
        private var _showExInfo:Boolean = false;
        private var _isColorBlind:Boolean = false;
        private var _splashDuration:int = 1000;
        private var _extraConfig:Object = null;

        public function VehicleMarkersManager()
        {
            super();
            _instance = this;
        }

        public static function getInstance() : VehicleMarkersManager
        {
            return _instance;
        }

        public function as_setExtraConfig(value:Object) : void
        {
            _extraConfig = value;
        }

        public function getExtraConfig() : Object
        {
            return _extraConfig;
        }

        public function as_setColorBlind(value:Boolean) : void
        {
            _isColorBlind = value;
        }

        public function as_setColorSchemes(defaultSchemes:Object, colorBlindSchemes:Object) : void
        {
        }

        public function as_setMarkerDuration(value:int) : void
        {
            _splashDuration = value;
        }

        public function as_setMarkerSettings(value:Object) : void
        {
        }

        public function as_setShowExInfoFlag(value:Boolean) : void
        {
            _showExInfo = value;
        }

        public function as_updateMarkersSettings() : void
        {
        }

        public function addMarker(id:Object, marker:VehicleMarker) : void
        {
            if(marker == null)
            {
                marker = new VehicleMarker();
            }
            markers[id] = marker;
            if(marker.parent == null)
            {
                addChild(marker);
            }
        }

        public function removeMarker(id:Object) : void
        {
            var marker:VehicleMarker = markers[id] as VehicleMarker;
            if(marker != null && marker.parent == this)
            {
                removeChild(marker);
            }
            delete markers[id];
        }

        public function getMarker(id:Object) : VehicleMarker
        {
            return markers[id] as VehicleMarker;
        }

        public function updateHealth(id:Object, newHealth:int, damageFrom:uint, damageType:String = "shot", maxHealth:int = -1) : void
        {
            var marker:VehicleMarker = getMarker(id);
            if(marker != null)
            {
                marker.updateHealth(newHealth, damageFrom, damageType, maxHealth);
            }
        }

        public function get showExInfo() : Boolean
        {
            return _showExInfo;
        }

        public function get isColorBlind() : Boolean
        {
            return _isColorBlind;
        }

        public function get splashDuration() : int
        {
            return _splashDuration;
        }
    }
}

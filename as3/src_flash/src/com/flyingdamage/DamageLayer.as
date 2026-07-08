package com.flyingdamage
{
    import flash.display.Sprite;

    public class DamageLayer extends Sprite
    {
        private var _app:FlyingDamageApp;
        private var _markers:Object;

        public function DamageLayer(app:FlyingDamageApp)
        {
            _app = app;
            _markers = {};
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function showDamage(vehicleID:String, damage:int, colorRGB:uint, fontSize:int, alpha:Number, startX:Number = 0, startY:Number = 0, hasStart:Boolean = false, hasHp:Boolean = false, hpCur:int = 0, hpBefore:int = 0, hpMax:int = 0, sourceFlag:uint = 0, damageType:String = "shot"):void
        {
            if (damage <= 0)
                return;

            var marker:VehicleMarkerCore = getMarker(vehicleID);
            marker.setMarkerSnapshot(startX, startY, hasStart);
            marker.updateHealth(damage, colorRGB, hasHp, hpCur, hpBefore, hpMax);
            marker.addDamageLabel(damage, colorRGB, fontSize, alpha, sourceFlag, damageType);
        }

        private function getMarker(vehicleID:String):VehicleMarkerCore
        {
            var marker:VehicleMarkerCore = _markers[vehicleID] as VehicleMarkerCore;
            if (marker == null)
            {
                marker = new VehicleMarkerCore(vehicleID);
                _markers[vehicleID] = marker;
                addChild(marker);
            }
            return marker;
        }

        public function clearAll():void
        {
            for each (var marker:VehicleMarkerCore in _markers)
            {
                if (marker.parent != null)
                    marker.parent.removeChild(marker);
                marker.dispose();
            }
            _markers = {};
        }

        public function tick():int
        {
            var count:int = 0;
            for (var id:String in _markers)
            {
                var marker:VehicleMarkerCore = _markers[id] as VehicleMarkerCore;
                if (marker == null)
                {
                    delete _markers[id];
                    continue;
                }
                var pos:Object = _app.getScreenPos(marker.vehicleID);
                if (marker.tick(pos))
                    count++;
                else
                {
                    if (marker.parent != null)
                        marker.parent.removeChild(marker);
                    marker.dispose();
                    delete _markers[id];
                }
            }
            return count;
        }
    }
}

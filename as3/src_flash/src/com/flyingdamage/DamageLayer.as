package com.flyingdamage
{
    import flash.display.Sprite;

    public class DamageLayer extends Sprite
    {
        private var _app:FlyingDamageApp;
        private var _events:Vector.<VehicleMarkerCore>;
        private var _eventSeq:int = 0;

        public function DamageLayer(app:FlyingDamageApp)
        {
            _app = app;
            _events = new Vector.<VehicleMarkerCore>();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function showDamage(vehicleID:String, damage:int, colorRGB:uint, fontSize:int, alpha:Number, startX:Number = 0, startY:Number = 0, hasStart:Boolean = false, hasHp:Boolean = false, hpCur:int = 0, hpBefore:int = 0, hpMax:int = 0, sourceFlag:uint = 0, damageType:String = "shot"):void
        {
            if (damage <= 0 && !VehicleMarkerFlags.checkLabeledDamages(damageType))
                return;

            // Important: create a separate marker-local core for every damage event.
            // Reusing one core per vehicle makes old labels jump when a later hit on
            // the same tank updates the container position.
            var marker:VehicleMarkerCore = new VehicleMarkerCore(vehicleID + "#" + (_eventSeq++), vehicleID);
            marker.setMarkerSnapshot(startX, startY, hasStart);
            marker.updateHealth(damage, colorRGB, hasHp, hpCur, hpBefore, hpMax);
            marker.addDamageLabel(damage, colorRGB, fontSize, alpha, sourceFlag, damageType);
            addChild(marker);
            _events.push(marker);
        }

        public function clearAll():void
        {
            for each (var marker:VehicleMarkerCore in _events)
            {
                if (marker.parent != null)
                    marker.parent.removeChild(marker);
                marker.dispose();
            }
            _events = new Vector.<VehicleMarkerCore>();
        }

        public function tick():int
        {
            var survivors:Vector.<VehicleMarkerCore> = new Vector.<VehicleMarkerCore>();
            for each (var marker:VehicleMarkerCore in _events)
            {
                var pos:Object = _app.getScreenPos(marker.vehicleID);
                if (marker.tick(pos))
                    survivors.push(marker);
                else
                {
                    if (marker.parent != null)
                        marker.parent.removeChild(marker);
                    marker.dispose();
                }
            }
            _events = survivors;
            return _events.length;
        }
    }
}

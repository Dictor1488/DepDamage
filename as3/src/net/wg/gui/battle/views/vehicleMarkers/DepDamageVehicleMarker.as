package net.wg.gui.battle.views.vehicleMarkers
{
    import com.flyingdamage.FloatingDamageLayer;
    import com.flyingdamage.FlyingDamageConfig;
    import flash.display.MovieClip;

    /**
     * VehicleMarker replacement with XVM-like floating damage text.
     *
     * The Python hook packs `damageType` as `attackReason,attackerID`.
     * This marker keeps the stock marker behaviour by calling super.updateHealth,
     * then renders our number inside the marker display tree.
     */
    public class DepDamageVehicleMarker extends VehicleMarker
    {
        private var _curHealth:Number = NaN;
        private var _damageLayer:FloatingDamageLayer;

        public function DepDamageVehicleMarker()
        {
            super();
            ensureDamageLayer();
        }

        override public function updateHealth(newHealth:int, damageFlag:uint, damageType:String, ramDamageThreshold:int = -1):void
        {
            var prevHealth:Number = _curHealth;
            _curHealth = newHealth;

            super.updateHealth(newHealth, damageFlag, damageType, ramDamageThreshold);

            if (isNaN(prevHealth))
                return;

            var damage:int = int(prevHealth - Math.max(newHealth, 0));
            if (damage <= 0)
                return;

            var unpacked:Object = unpackDamageType(damageType);
            ensureDamageLayer();
            _damageLayer.showDamage(
                damage,
                unpacked.attackerID,
                unpacked.damageType,
                int(damageFlag),
                FlyingDamageConfig.DEFAULT_X,
                FlyingDamageConfig.DEFAULT_Y
            );
        }

        override public function setHealth(curHealth:int):void
        {
            _curHealth = curHealth;
            super.setHealth(curHealth);
        }

        private function ensureDamageLayer():void
        {
            if (_damageLayer == null)
            {
                _damageLayer = new FloatingDamageLayer();
                addChild(_damageLayer);
            }
            else if (_damageLayer.parent != this)
            {
                addChild(_damageLayer);
            }
        }

        private function unpackDamageType(value:String):Object
        {
            var result:Object = {
                damageType: value,
                attackerID: 0
            };
            if (value == null)
                return result;
            var parts:Array = value.split(',');
            if (parts.length > 0)
                result.damageType = parts[0];
            if (parts.length > 1)
                result.attackerID = Number(parts[1]);
            return result;
        }
    }
}

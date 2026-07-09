package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;

    public final class FloatingDamageLayer extends Sprite
    {
        private var _lastByAttacker:Dictionary = new Dictionary();

        public function FloatingDamageLayer()
        {
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function showDamage(damage:int, attackerID:Number, damageType:String, damageFlag:int, xPos:Number = 0, yPos:Number = -67):void
        {
            if (damage <= 0)
                return;

            var key:String = String(attackerID) + ':' + damageType;
            var now:int = getTimer();
            var prev:Object = _lastByAttacker[key];

            if (prev && prev.mc && prev.mc.parent && (now - prev.time) < FlyingDamageConfig.MERGE_TIME_MS)
            {
                prev.damage += damage;
                prev.time = now;
                prev.mc.setDamage(prev.damage, formatDamage(prev.damage, damageFlag));
                return;
            }

            var mc:FloatingDamageNumber = new FloatingDamageNumber(
                formatDamage(damage, damageFlag),
                damage,
                xPos,
                yPos,
                FlyingDamageConfig.DEFAULT_SPEED,
                FlyingDamageConfig.DEFAULT_MAX_RANGE
            );
            addChild(mc);

            _lastByAttacker[key] = {
                mc: mc,
                damage: damage,
                time: now
            };
        }

        private function formatDamage(value:int, damageFlag:int):String
        {
            var color:String = '#FFFFFF';
            if (damageFlag == 1)
                color = '#FFDD66';
            else if (damageFlag == 2)
                color = '#99CCFF';
            else if (damageFlag == 4)
                color = '#FF6666';
            return '<font color="' + color + '">' + value.toString() + '</font>';
        }
    }
}

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

        public function showDamage(damage:int, attackerID:Number, damageType:String, xPos:Number = 0, yPos:Number = -67):void
        {
            if (damage <= 0)
                return;

            var key:String = String(attackerID) + ':' + damageType;
            var now:int = getTimer();
            var prev:Object = _lastByAttacker[key];

            if (prev && prev.mc && (now - prev.time) < FlyingDamageConfig.MERGE_TIME_MS)
            {
                prev.damage += damage;
                prev.time = now;
                prev.mc.setDamage(prev.damage, formatDamage(prev.damage));
                return;
            }

            var mc:FloatingDamageNumber = new FloatingDamageNumber(
                formatDamage(damage),
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

        private function formatDamage(value:int):String
        {
            return '<font color="#FFFFFF">' + value.toString() + '</font>';
        }
    }
}

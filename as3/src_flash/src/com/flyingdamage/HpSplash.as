package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.utils.getTimer;

    public class HpSplash extends Sprite
    {
        public var vehicleID:String;

        private var _bornAt:int;
        private var _part:HealthBarAnimatedPart;

        public function HpSplash(vehicleID:String, damage:int, color:uint, hasHp:Boolean = false, hpCur:int = 0, hpBefore:int = 0, hpMax:int = 0)
        {
            this.vehicleID = vehicleID;
            _bornAt = getTimer();

            mouseEnabled = false;
            mouseChildren = false;

            _part = new HealthBarAnimatedPart(damage, color, hasHp, hpCur, hpBefore, hpMax);
            addChild(_part);
            visible = true;
        }

        public function update():Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (_part == null || !_part.update(age))
                return false;

            visible = true;
            x = 0;
            y = HealthBarAnimatedPart.DMG_BAR_Y;
            return true;
        }

        public function dispose():void
        {
            if (_part != null)
            {
                if (_part.parent != null)
                    _part.parent.removeChild(_part);
                _part.dispose();
                _part = null;
            }
        }
    }
}

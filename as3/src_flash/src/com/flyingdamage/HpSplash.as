package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.utils.getTimer;

    public class HpSplash extends Sprite
    {
        public var vehicleID:String;

        private var _bornAt:int;
        private var _markerX:Number = 0;
        private var _markerY:Number = 0;
        private var _hasMarker:Boolean = false;
        private var _part:HealthBarAnimatedPart;

        public function HpSplash(vehicleID:String, damage:int, color:uint, startX:Number = 0, startY:Number = 0, hasStart:Boolean = false, hasHp:Boolean = false, hpCur:int = 0, hpBefore:int = 0, hpMax:int = 0)
        {
            this.vehicleID = vehicleID;
            _markerX = startX;
            _markerY = startY;
            _hasMarker = hasStart;
            _bornAt = getTimer();

            mouseEnabled = false;
            mouseChildren = false;

            _part = new HealthBarAnimatedPart(damage, color, hasHp, hpCur, hpBefore, hpMax);
            addChild(_part);

            visible = _hasMarker;
        }

        public function update(pos:Object):Boolean
        {
            var age:Number = (getTimer() - _bornAt) / 1000.0;
            if (_part == null || !_part.update(age))
                return false;

            // Same mode as FloatingNumber: hit-time marker snapshot.
            if (!_hasMarker && pos != null && pos.ok)
            {
                _markerX = Number(pos.x);
                _markerY = Number(pos.y);
                _hasMarker = true;
            }

            if (!_hasMarker)
            {
                visible = false;
                return true;
            }

            visible = true;
            x = _markerX;
            y = _markerY + HealthBarAnimatedPart.DMG_BAR_Y;
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

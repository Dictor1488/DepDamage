package com.flyingdamage
{
    import flash.display.Sprite;

    public class DamageLayer extends Sprite
    {
        private var _app:FlyingDamageApp;
        private var _items:Vector.<FloatingNumber>;
        private var _logCount:int = 0;

        public function DamageLayer(app:FlyingDamageApp)
        {
            _app = app;
            _items = new Vector.<FloatingNumber>();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function showScreenDamage(x:Number, y:Number, damage:int,
                                         colorRGB:uint, fontSize:int,
                                         alpha:Number, rise:Number,
                                         life:Number):void
        {
            if (damage <= 0)
                return;
            var fn:FloatingNumber = FloatingNumber.createScreen(_app, x, y, damage,
                                                                colorRGB, fontSize,
                                                                alpha, rise, life);
            addChild(fn);
            _items.push(fn);
            log("DamageLayer add screen d=" + damage + " items=" + _items.length + " children=" + numChildren + " pos=(" + x + "," + y + ")");
        }

        public function showWorldDamage(wx:Number, wy:Number, wz:Number,
                                        fallbackX:Number, fallbackY:Number,
                                        damage:int, colorRGB:uint,
                                        fontSize:int, alpha:Number,
                                        rise:Number, life:Number):void
        {
            if (damage <= 0)
                return;
            var fn:FloatingNumber = FloatingNumber.createWorld(_app, wx, wy, wz,
                                                               fallbackX, fallbackY,
                                                               damage, colorRGB,
                                                               fontSize, alpha,
                                                               rise, life);
            addChild(fn);
            _items.push(fn);
            log("DamageLayer add world d=" + damage + " items=" + _items.length + " children=" + numChildren + " fallback=(" + fallbackX + "," + fallbackY + ")");
        }

        public function showVehicleDamage(vehicleID:int,
                                          fallbackX:Number, fallbackY:Number,
                                          damage:int, colorRGB:uint,
                                          fontSize:int, alpha:Number,
                                          riseMeters:Number, life:Number):void
        {
            if (damage <= 0)
                return;
            var fn:FloatingNumber = FloatingNumber.createVehicle(_app, vehicleID,
                                                                 fallbackX, fallbackY,
                                                                 damage, colorRGB,
                                                                 fontSize, alpha,
                                                                 riseMeters, life);
            addChild(fn);
            _items.push(fn);
            log("DamageLayer add vehicle vid=" + vehicleID + " d=" + damage + " items=" + _items.length + " children=" + numChildren + " fallback=(" + fallbackX + "," + fallbackY + ") rise=" + riseMeters);
        }

        public function clearAll():void
        {
            for each (var fn:FloatingNumber in _items)
            {
                if (fn.parent != null)
                    fn.parent.removeChild(fn);
                fn.dispose();
            }
            _items = new Vector.<FloatingNumber>();
        }

        public function tick():int
        {
            var survivors:Vector.<FloatingNumber> = new Vector.<FloatingNumber>();
            for each (var fn:FloatingNumber in _items)
            {
                if (fn.update())
                    survivors.push(fn);
                else
                {
                    if (fn.parent != null)
                        fn.parent.removeChild(fn);
                    fn.dispose();
                }
            }
            _items = survivors;
            if (_logCount < 20 && _items.length > 0)
            {
                _logCount++;
                log("DamageLayer tick items=" + _items.length + " children=" + numChildren + " visible=" + visible + " alpha=" + alpha);
            }
            return _items.length;
        }

        private function log(msg:String):void
        {
            try { if (_app != null) _app.debugLog(msg); }
            catch (e:Error) {}
        }
    }
}
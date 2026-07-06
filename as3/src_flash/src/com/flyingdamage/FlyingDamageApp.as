package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.TimerEvent;
    import flash.utils.Timer;

    /**
     * FlyingDamageApp -- ExternalFlashComponent.
     *
     * Uses primitive AS calls from Python. Passing Python dict/Object through
     * Scaleform was not reliable on the current client, so damage is pushed as
     * separate Number/int arguments.
     */
    public class FlyingDamageApp extends Sprite
    {
        public var py_getScreenPos:Function = null;
        public var py_projectWorld:Function = null;
        public var py_pullDamage:Function = null;
        public var py_log:Function = null;

        private var _layer:DamageLayer = null;
        private var _timer:Timer = null;
        private var _debugShown:int = 0;

        public function FlyingDamageApp()
        {
            super();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function as_populate():void
        {
            _ensureLayer();
            if (_timer == null)
            {
                _timer = new Timer(16);
                _timer.addEventListener(TimerEvent.TIMER, onTick);
            }
            _timer.start();
            log("as_populate (timer started)");
        }

        public function as_showDamageScreen(x:Number, y:Number, damage:int,
                                            colorRGB:uint, fontSize:int,
                                            alpha:Number, rise:Number,
                                            life:Number):void
        {
            _ensureLayer();
            try
            {
                _layer.showScreenDamage(x, y, damage, colorRGB, fontSize, alpha, rise, life);
                _debugShown++;
                if (_debugShown <= 12)
                    log("as_showDamageScreen d=" + damage + " x=" + x + " y=" + y);
            }
            catch (e:Error)
            {
                log("as_showDamageScreen error: " + e.message);
            }
        }

        public function as_showDamageWorld(wx:Number, wy:Number, wz:Number,
                                           fallbackX:Number, fallbackY:Number,
                                           damage:int, colorRGB:uint,
                                           fontSize:int, alpha:Number,
                                           rise:Number, life:Number):void
        {
            _ensureLayer();
            try
            {
                _layer.showWorldDamage(wx, wy, wz, fallbackX, fallbackY, damage,
                                       colorRGB, fontSize, alpha, rise, life);
                _debugShown++;
                if (_debugShown <= 12)
                    log("as_showDamageWorld d=" + damage + " x=" + fallbackX + " y=" + fallbackY);
            }
            catch (e:Error)
            {
                log("as_showDamageWorld error: " + e.message);
            }
        }

        public function as_clear():void
        {
            if (_layer != null)
                _layer.clearAll();
        }

        public function as_dispose():void
        {
            if (_timer != null)
            {
                _timer.stop();
                _timer.removeEventListener(TimerEvent.TIMER, onTick);
                _timer = null;
            }
            if (_layer != null)
            {
                _layer.clearAll();
                if (_layer.parent != null) _layer.parent.removeChild(_layer);
                _layer = null;
            }
            py_getScreenPos = null;
            py_projectWorld = null;
            py_pullDamage = null;
            py_log = null;
        }

        public function projectWorld(wx:Number, wy:Number, wz:Number):Object
        {
            if (py_projectWorld == null)
                return null;
            try { return py_projectWorld(wx, wy, wz); }
            catch (e:Error) {}
            return null;
        }

        private function _ensureLayer():void
        {
            if (_layer == null)
            {
                _layer = new DamageLayer(this);
                addChild(_layer);
            }
        }

        private function onTick(e:TimerEvent):void
        {
            if (_layer == null)
                return;
            _layer.tick();
        }

        private function log(msg:String):void
        {
            try { if (py_log != null) py_log("[SWF] " + msg); }
            catch (e:Error) {}
        }
    }
}

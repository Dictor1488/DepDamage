package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.events.TimerEvent;
    import flash.utils.Timer;

    /**
     * FlyingDamageApp -- Sprite overlay (ExternalFlashComponent). Data flows via
     * PULL. We drive updates with a Timer (~60fps) instead of ENTER_FRAME, since
     * ENTER_FRAME may not fire reliably for this component.
     */
    public class FlyingDamageApp extends Sprite
    {
        public var py_getScreenPos:Function = null;
        public var py_pullDamage:Function = null;
        public var py_log:Function = null;

        private var _layer:DamageLayer = null;
        private var _timer:Timer = null;

        public function FlyingDamageApp()
        {
            super();
        }

        public function as_populate():void
        {
            _ensureLayer();
            if (_timer == null)
            {
                _timer = new Timer(16);  // ~60 fps
                _timer.addEventListener(TimerEvent.TIMER, onTick);
            }
            _timer.start();
            log("as_populate (timer started)");
        }

        public function as_dispose():void
        {
            if (_timer != null)
            {
                _timer.stop();
                _timer.removeEventListener(TimerEvent.TIMER, onTick);
                _timer = null;
            }
            if (_layer)
            {
                _layer.clearAll();
                if (_layer.parent) _layer.parent.removeChild(_layer);
                _layer = null;
            }
            py_getScreenPos = null;
            py_pullDamage = null;
            py_log = null;
        }

        public function getScreenPos(vehicleID:String):Object
        {
            if (py_getScreenPos == null)
                return null;
            try { return py_getScreenPos(vehicleID); }
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

            if (py_pullDamage != null)
            {
                try
                {
                    var list:Object = py_pullDamage();
                    if (list != null && list.length > 0)
                    {
                        for (var i:int = 0; i < list.length; i++)
                        {
                            var d:Object = list[i];
                            log("recv vid=" + d.vid + " dmg=" + d.dmg);
                            _layer.showDamage(String(d.vid), int(d.dmg),
                                uint(d.color), int(d.size), Number(d.alpha));
                        }
                    }
                }
                catch (err:Error)
                {
                    log("pull error: " + err.message);
                }
            }

            _layer.tick();
        }

        private function log(msg:String):void
        {
            try { if (py_log != null) py_log("[SWF] " + msg); }
            catch (e:Error) {}
        }
    }
}

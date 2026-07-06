package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.TimerEvent;
    import flash.utils.Timer;

    /**
     * FlyingDamageApp -- ExternalFlashComponent.
     *
     * Damage can arrive in two ways:
     *   1) direct Python -> AS3 call: as_showDamage(data)
     *   2) fallback pull queue: py_pullDamage()
     *
     * Direct push is preferred because some Scaleform external components do not
     * reliably execute polling callbacks every frame in battle.
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

        public function as_showDamage(data:Object):void
        {
            _ensureLayer();
            if (data == null)
                return;
            try
            {
                _layer.showDamage(data);
                _debugShown++;
                if (_debugShown <= 8)
                    log("as_showDamage d=" + data.dmg + " mode=" + data.mode + " x=" + data.x + " y=" + data.y);
            }
            catch (e:Error)
            {
                log("as_showDamage error: " + e.message);
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
                            as_showDamage(list[i]);
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

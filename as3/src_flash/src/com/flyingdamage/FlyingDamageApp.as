package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.TimerEvent;
    import flash.utils.Timer;
    import flash.display.StageAlign;
    import flash.display.StageScaleMode;

    /**
     * FlyingDamageApp -- ExternalFlashComponent.
     *
     * GUI.Flash is centered by its SWF dimensions. The root sprite is shifted so
     * the 800x600 SWF can cover the real screen. Therefore all screen pixel
     * coordinates from Python must be converted to this corrected local space.
     */
    public class FlyingDamageApp extends Sprite
    {
        private static const SWF_HALF_WIDTH:Number = 400.0;
        private static const SWF_HALF_HEIGHT:Number = 300.0;

        public var py_getScreenPos:Function = null;
        public var py_projectWorld:Function = null;
        public var py_pullDamageText:Function = null;
        public var py_log:Function = null;

        private var _layer:DamageLayer = null;
        private var _timer:Timer = null;
        private var _debugShown:int = 0;
        private var _selfTestShown:Boolean = false;
        private var _positionLogged:Boolean = false;
        private var _pullLogged:int = 0;

        public function FlyingDamageApp()
        {
            super();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function as_populate():void
        {
            try
            {
                if (stage != null)
                {
                    stage.scaleMode = StageScaleMode.NO_SCALE;
                    stage.align = StageAlign.TOP_LEFT;
                    log("stage size=" + stage.stageWidth + "x" + stage.stageHeight);
                }
            }
            catch (e:Error) {}

            _ensureLayer();
            _updateAppPosition();

            if (_timer == null)
            {
                _timer = new Timer(16);
                _timer.addEventListener(TimerEvent.TIMER, onTick);
            }
            _timer.start();
            log("as_populate (timer started, polling queue)");

            if (!_selfTestShown)
            {
                _selfTestShown = true;
                // Show near the real screen centre. as_showDamageScreen converts
                // this screen-space point to SWF-local coordinates.
                as_showDamageScreen(stage != null ? stage.stageWidth / 2.0 : 1280,
                                    stage != null ? stage.stageHeight / 2.0 : 684,
                                    8888, 0x00FFFF, 42, 1.0, 80, 4.0);
            }
        }

        public function as_showDamageScreen(x:Number, y:Number, damage:int,
                                            colorRGB:uint, fontSize:int,
                                            alpha:Number, rise:Number,
                                            life:Number):void
        {
            _ensureLayer();
            _updateAppPosition();
            try
            {
                var lx:Number = _screenToLocalX(x);
                var ly:Number = _screenToLocalY(y);
                _layer.showScreenDamage(lx, ly, damage, colorRGB, fontSize, alpha, rise, life);
                _debugShown++;
                if (_debugShown <= 24)
                    log("as_showDamageScreen d=" + damage + " screen=(" + x + "," + y + ") local=(" + lx + "," + ly + ") root=(" + this.x + "," + this.y + ")");
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
            _updateAppPosition();
            try
            {
                var lx:Number = _screenToLocalX(fallbackX);
                var ly:Number = _screenToLocalY(fallbackY);
                _layer.showWorldDamage(wx, wy, wz, lx, ly, damage,
                                       colorRGB, fontSize, alpha, rise, life);
                _debugShown++;
                if (_debugShown <= 24)
                    log("as_showDamageWorld d=" + damage + " screen=(" + fallbackX + "," + fallbackY + ") local=(" + lx + "," + ly + ") root=(" + this.x + "," + this.y + ")");
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
            py_pullDamageText = null;
            py_log = null;
        }

        public function projectWorld(wx:Number, wy:Number, wz:Number):Object
        {
            if (py_projectWorld == null)
                return null;
            try
            {
                var pos:Object = py_projectWorld(wx, wy, wz);
                if (pos != null && pos.ok)
                {
                    pos.x = _screenToLocalX(Number(pos.x));
                    pos.y = _screenToLocalY(Number(pos.y));
                }
                return pos;
            }
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

        private function _updateAppPosition():void
        {
            if (stage == null)
                return;

            var sw:Number = stage.stageWidth;
            var sh:Number = stage.stageHeight;
            this.x = SWF_HALF_WIDTH - (sw / 2.0);
            this.y = SWF_HALF_HEIGHT - (sh / 2.0);

            if (!_positionLogged)
            {
                _positionLogged = true;
                log("root corrected to x=" + this.x + " y=" + this.y + " for screen=" + sw + "x" + sh);
            }
        }

        private function _screenToLocalX(screenX:Number):Number
        {
            return screenX - this.x;
        }

        private function _screenToLocalY(screenY:Number):Number
        {
            return screenY - this.y;
        }

        private function onTick(e:TimerEvent):void
        {
            if (_layer == null)
                return;
            _updateAppPosition();
            _pullDamageQueue();
            _layer.tick();
        }

        private function _pullDamageQueue():void
        {
            if (py_pullDamageText == null)
                return;

            var data:String = "";
            try { data = String(py_pullDamageText()); }
            catch (e:Error)
            {
                log("py_pullDamageText error: " + e.message);
                return;
            }

            if (data == null || data.length == 0)
                return;

            if (_pullLogged < 20)
            {
                _pullLogged++;
                log("pulled damage data: " + data);
            }

            var rows:Array = data.split("\n");
            for each (var row:String in rows)
            {
                _parseDamageRow(row);
            }
        }

        private function _parseDamageRow(row:String):void
        {
            if (row == null || row.length == 0)
                return;

            var p:Array = row.split("|");
            try
            {
                if (p[0] == "S" && p.length >= 9)
                {
                    as_showDamageScreen(Number(p[1]), Number(p[2]), int(p[3]), uint(p[4]),
                                        int(p[5]), Number(p[6]), Number(p[7]), Number(p[8]));
                }
                else if (p[0] == "W" && p.length >= 12)
                {
                    as_showDamageWorld(Number(p[1]), Number(p[2]), Number(p[3]),
                                       Number(p[4]), Number(p[5]), int(p[6]), uint(p[7]),
                                       int(p[8]), Number(p[9]), Number(p[10]), Number(p[11]));
                }
            }
            catch (e:Error)
            {
                log("parse damage row error: " + e.message + " row=" + row);
            }
        }

        private function log(msg:String):void
        {
            try { if (py_log != null) py_log("[SWF] " + msg); }
            catch (e:Error) {}
        }
    }
}

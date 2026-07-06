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
     * On the current WoT client stage.stageWidth/stage.stageHeight already match
     * the real screen size. Root shifting makes objects disappear, so this build
     * uses native stage/screen coordinates directly.
     */
    public class FlyingDamageApp extends Sprite
    {
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
        private var _emptyPollLogged:Boolean = false;

        public function FlyingDamageApp()
        {
            super();
            x = 0;
            y = 0;
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
            log("as_populate (timer started, no root shift, polling queue)");

            if (!_selfTestShown)
            {
                _selfTestShown = true;
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
                _layer.showScreenDamage(x, y, damage, colorRGB, fontSize, alpha, rise, life);
                _debugShown++;
                if (_debugShown <= 30)
                    log("as_showDamageScreen d=" + damage + " screen=(" + x + "," + y + ") root=(" + this.x + "," + this.y + ")");
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
                _layer.showWorldDamage(wx, wy, wz, fallbackX, fallbackY, damage,
                                       colorRGB, fontSize, alpha, rise, life);
                _debugShown++;
                if (_debugShown <= 30)
                    log("as_showDamageWorld d=" + damage + " screen=(" + fallbackX + "," + fallbackY + ") root=(" + this.x + "," + this.y + ")");
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

        private function _updateAppPosition():void
        {
            this.x = 0;
            this.y = 0;
            if (!_positionLogged)
            {
                _positionLogged = true;
                if (stage != null)
                    log("root forced to 0,0 for screen=" + stage.stageWidth + "x" + stage.stageHeight);
                else
                    log("root forced to 0,0");
            }
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
            {
                if (!_emptyPollLogged)
                {
                    _emptyPollLogged = true;
                    log("py_pullDamageText is null");
                }
                return;
            }

            var data:String = "";
            try { data = String(py_pullDamageText()); }
            catch (e:Error)
            {
                log("py_pullDamageText error: " + e.message);
                return;
            }

            if (data == null || data.length == 0)
                return;

            if (_pullLogged < 30)
            {
                _pullLogged++;
                log("pulled damage data: " + data);
            }

            var rows:Array = data.split("\n");
            for each (var row:String in rows)
                _parseDamageRow(row);
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

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
     * Python queues damage events. AS3 renders visible flying numbers and, for
     * vehicle anchored events, asks Python for the current screen projection of
     * the damaged vehicle every tick.
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
            log("as_populate (timer started, vehicle-anchored coordinates)");
        }

        public function as_showDamageScreen(x:Number, y:Number, damage:int,
                                            colorRGB:uint, fontSize:int,
                                            alpha:Number, rise:Number,
                                            life:Number):void
        {
            if (_isNormalized(x, y))
                as_showDamageNormalized(x, y, damage, colorRGB, fontSize, alpha, rise, life);
            else
                _showDamagePixels(x, y, damage, colorRGB, fontSize, alpha, rise, life, "screen");
        }

        public function as_showDamageNormalized(nx:Number, ny:Number, damage:int,
                                                colorRGB:uint, fontSize:int,
                                                alpha:Number, riseNorm:Number,
                                                life:Number):void
        {
            var px:Number = _stageW() * nx;
            var py:Number = _stageH() * ny;
            var risePx:Number = _stageH() * riseNorm;
            _showDamagePixels(px, py, damage, colorRGB, fontSize, alpha, risePx, life, "norm");
        }

        private function _showDamagePixels(px:Number, py:Number, damage:int,
                                           colorRGB:uint, fontSize:int,
                                           alpha:Number, rise:Number,
                                           life:Number, mode:String):void
        {
            _ensureLayer();
            _updateAppPosition();
            try
            {
                _layer.showScreenDamage(px, py, damage, colorRGB, fontSize, alpha, rise, life);
                _debugShown++;
                if (_debugShown <= 40)
                    log("showDamage " + mode + " d=" + damage + " px=(" + px + "," + py + ") stage=(" + _stageW() + "," + _stageH() + ") root=(" + this.x + "," + this.y + ")");
            }
            catch (e:Error)
            {
                log("showDamage error: " + e.message);
            }
        }

        public function as_showDamageWorld(wx:Number, wy:Number, wz:Number,
                                           fallbackNX:Number, fallbackNY:Number,
                                           damage:int, colorRGB:uint,
                                           fontSize:int, alpha:Number,
                                           rise:Number, life:Number):void
        {
            _ensureLayer();
            _updateAppPosition();
            try
            {
                _layer.showWorldDamage(wx, wy, wz, _stageW() * fallbackNX, _stageH() * fallbackNY,
                                       damage, colorRGB, fontSize, alpha, rise, life);
                _debugShown++;
                if (_debugShown <= 40)
                    log("as_showDamageWorld d=" + damage + " norm=(" + fallbackNX + "," + fallbackNY + ") stage=(" + _stageW() + "," + _stageH() + ")");
            }
            catch (e:Error)
            {
                log("as_showDamageWorld error: " + e.message);
            }
        }

        public function as_showDamageVehicle(vehicleID:int,
                                             fallbackNX:Number, fallbackNY:Number,
                                             damage:int, colorRGB:uint,
                                             fontSize:int, alpha:Number,
                                             riseMeters:Number, life:Number):void
        {
            _ensureLayer();
            _updateAppPosition();
            try
            {
                _layer.showVehicleDamage(vehicleID, _stageW() * fallbackNX, _stageH() * fallbackNY,
                                         damage, colorRGB, fontSize, alpha, riseMeters, life);
                _debugShown++;
                if (_debugShown <= 40)
                    log("as_showDamageVehicle vid=" + vehicleID + " d=" + damage + " norm=(" + fallbackNX + "," + fallbackNY + ") stage=(" + _stageW() + "," + _stageH() + ")");
            }
            catch (e:Error)
            {
                log("as_showDamageVehicle error: " + e.message);
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

        public function projectVehicle(vehicleID:int, riseMeters:Number):Object
        {
            if (py_getScreenPos == null)
                return null;
            try
            {
                var pos:Object = py_getScreenPos(vehicleID, riseMeters);
                if (pos != null && pos.ok && pos.normalized)
                {
                    pos.x = _stageW() * Number(pos.x);
                    pos.y = _stageH() * Number(pos.y);
                }
                return pos;
            }
            catch (e:Error) {}
            return null;
        }

        public function projectWorld(wx:Number, wy:Number, wz:Number):Object
        {
            if (py_projectWorld == null)
                return null;
            try
            {
                var pos:Object = py_projectWorld(wx, wy, wz);
                if (pos != null && pos.ok && pos.normalized)
                {
                    pos.x = _stageW() * Number(pos.x);
                    pos.y = _stageH() * Number(pos.y);
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
            this.x = 0;
            this.y = 0;
            if (!_positionLogged)
            {
                _positionLogged = true;
                log("root 0,0; vehicle anchored render; stage=" + _stageW() + "x" + _stageH());
            }
        }

        private function _stageW():Number
        {
            return stage != null && stage.stageWidth > 0 ? stage.stageWidth : 1920;
        }

        private function _stageH():Number
        {
            return stage != null && stage.stageHeight > 0 ? stage.stageHeight : 1080;
        }

        private function _isNormalized(x:Number, y:Number):Boolean
        {
            return x >= -0.25 && x <= 1.25 && y >= -0.25 && y <= 1.25;
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
                if (p[0] == "N" && p.length >= 9)
                {
                    as_showDamageNormalized(Number(p[1]), Number(p[2]), int(p[3]), uint(p[4]),
                                            int(p[5]), Number(p[6]), Number(p[7]), Number(p[8]));
                }
                else if (p[0] == "S" && p.length >= 9)
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
                else if (p[0] == "V" && p.length >= 10)
                {
                    as_showDamageVehicle(int(p[1]), Number(p[2]), Number(p[3]), int(p[4]), uint(p[5]),
                                         int(p[6]), Number(p[7]), Number(p[8]), Number(p[9]));
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
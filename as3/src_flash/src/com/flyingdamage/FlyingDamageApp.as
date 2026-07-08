package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.events.Event;

    public class FlyingDamageApp extends Sprite
    {
        public var py_getScreenPos:Function = null;
        public var py_pullDamage:Function = null;
        public var py_log:Function = null;

        private var _layer:DamageLayer = null;
        private var _populates:int = 0;
        private var _loggedFrame:int = 0;

        public function FlyingDamageApp()
        {
            super();
            mouseEnabled = false;
            mouseChildren = false;
            addEventListener(Event.ADDED_TO_STAGE, onAdded);
            addEventListener(Event.ENTER_FRAME, onFrame);
        }

        private function onAdded(e:Event):void
        {
            log("ADDED_TO_STAGE populate-driven-render stage=" + stageSizeText());
            if (stage != null)
            {
                stage.frameRate = 60;
                stage.addEventListener(Event.ENTER_FRAME, onFrame);
            }
            _ensureLayer();
            pullAndTick();
        }

        private function onFrame(e:Event):void
        {
            if (_loggedFrame < 2)
            {
                _loggedFrame++;
                log("ENTER_FRAME populate-driven-render #" + _loggedFrame + " stage=" + stageSizeText());
            }
            pullAndTick();
        }

        public function as_populate():void
        {
            _populates++;
            _ensureLayer();
            log("as_populate TICK BUILD=populate-driven-render count=" + _populates + " stage=" + stageSizeText());
            pullAndTick();
        }

        public function as_update():void
        {
            pullAndTick();
        }

        private function pullAndTick():void
        {
            _ensureLayer();
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
                            var hasStart:Boolean = d.hasStart === true;
                            var screenW:Number = d.screenW != null ? Number(d.screenW) : 0;
                            var screenH:Number = d.screenH != null ? Number(d.screenH) : 0;
                            var rawX:Number = hasStart ? Number(d.x) : 0;
                            var rawY:Number = hasStart ? Number(d.y) : 0;
                            var sx:Number = hasStart ? normalizeX(rawX, screenW) : 0;
                            var sy:Number = hasStart ? normalizeY(rawY, screenH) : 0;
                            var hasHp:Boolean = d.hasHp === true;
                            var hpCur:int = hasHp ? int(d.hpCur) : 0;
                            var hpBefore:int = hasHp ? int(d.hpBefore) : 0;
                            var hpMax:int = hasHp ? int(d.hpMax) : 0;
                            var sourceFlag:uint = d.sourceFlag != null ? uint(d.sourceFlag) : VehicleMarkerFlags.DAMAGE_FROM_OTHER_FLAG;
                            var damageType:String = d.damageType != null ? String(d.damageType) : VehicleMarkerFlags.DAMAGE_SHOT;
                            log("recv vid=" + d.vid + " dmg=" + d.dmg + " hasStart=" + hasStart + " raw=(" + rawX.toFixed(1) + "," + rawY.toFixed(1) + ") norm=(" + sx.toFixed(1) + "," + sy.toFixed(1) + ") screen=(" + screenW.toFixed(1) + "," + screenH.toFixed(1) + ") stage=" + stageSizeText() + " hasHp=" + hasHp + " source=" + sourceFlag + " type=" + damageType);
                            _layer.showDamage(String(d.vid), int(d.dmg), uint(d.color), int(d.size), Number(d.alpha), sx, sy, hasStart, hasHp, hpCur, hpBefore, hpMax, sourceFlag, damageType);
                        }
                    }
                }
                catch (err:Error)
                {
                    log("pull error: " + err.message);
                }
            }
            if (_layer != null)
                _layer.tick();
        }

        public function as_dispose():void
        {
            if (stage != null)
                stage.removeEventListener(Event.ENTER_FRAME, onFrame);
            removeEventListener(Event.ENTER_FRAME, onFrame);
            if (_layer != null)
            {
                _layer.clearAll();
                if (_layer.parent != null)
                    _layer.parent.removeChild(_layer);
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
            try
            {
                var p:Object = py_getScreenPos(vehicleID);
                if (p == null)
                    return null;
                var sw:Number = p.screenW != null ? Number(p.screenW) : 0;
                var sh:Number = p.screenH != null ? Number(p.screenH) : 0;
                return {
                    ok: p.ok === true,
                    x: normalizeX(Number(p.x), sw),
                    y: normalizeY(Number(p.y), sh),
                    screenW: sw,
                    screenH: sh
                };
            }
            catch (e:Error) {}
            return null;
        }

        private function normalizeX(x:Number, sourceW:Number):Number
        {
            if (stage != null && sourceW > 0 && stage.stageWidth > 0 && Math.abs(sourceW - stage.stageWidth) > 1)
                return x * Number(stage.stageWidth) / sourceW;
            return x;
        }

        private function normalizeY(y:Number, sourceH:Number):Number
        {
            if (stage != null && sourceH > 0 && stage.stageHeight > 0 && Math.abs(sourceH - stage.stageHeight) > 1)
                return y * Number(stage.stageHeight) / sourceH;
            return y;
        }

        private function stageSizeText():String
        {
            if (stage == null)
                return "null";
            return String(stage.stageWidth) + "x" + String(stage.stageHeight);
        }

        private function _ensureLayer():void
        {
            if (_layer == null)
            {
                _layer = new DamageLayer(this);
                addChild(_layer);
                log("DamageLayer created populate-driven");
            }
        }

        private function log(msg:String):void
        {
            try
            {
                if (py_log != null)
                    py_log("[SWF] " + msg);
            }
            catch (e:Error) {}
        }
    }
}

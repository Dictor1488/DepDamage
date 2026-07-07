package com.flyingdamage
{
    import flash.display.Sprite;

    public class DamageLayer extends Sprite
    {
        private var _app:FlyingDamageApp;
        private var _items:Vector.<FloatingNumber>;
        private var _splashes:Vector.<HpSplash>;

        public function DamageLayer(app:FlyingDamageApp)
        {
            _app = app;
            _items = new Vector.<FloatingNumber>();
            _splashes = new Vector.<HpSplash>();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function showDamage(vehicleID:String, damage:int, colorRGB:uint, fontSize:int, alpha:Number, startX:Number = 0, startY:Number = 0, hasStart:Boolean = false, hasHp:Boolean = false, hpCur:int = 0, hpBefore:int = 0, hpMax:int = 0):void
        {
            if (damage <= 0)
                return;

            var splash:HpSplash = new HpSplash(vehicleID, damage, colorRGB, startX, startY, hasStart, hasHp, hpCur, hpBefore, hpMax);
            addChild(splash);
            _splashes.push(splash);

            var fn:FloatingNumber = new FloatingNumber(vehicleID, damage, colorRGB, fontSize, alpha, startX, startY, hasStart);
            addChild(fn);
            _items.push(fn);
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

            for each (var sp:HpSplash in _splashes)
            {
                if (sp.parent != null)
                    sp.parent.removeChild(sp);
                sp.dispose();
            }
            _splashes = new Vector.<HpSplash>();
        }

        public function tick():int
        {
            var survivors:Vector.<FloatingNumber> = new Vector.<FloatingNumber>();
            for each (var fn:FloatingNumber in _items)
            {
                var pos:Object = _app.getScreenPos(fn.vehicleID);
                if (fn.update(pos))
                    survivors.push(fn);
                else
                {
                    if (fn.parent != null)
                        fn.parent.removeChild(fn);
                    fn.dispose();
                }
            }
            _items = survivors;

            var splashSurvivors:Vector.<HpSplash> = new Vector.<HpSplash>();
            for each (var sp:HpSplash in _splashes)
            {
                var spos:Object = _app.getScreenPos(sp.vehicleID);
                if (sp.update(spos))
                    splashSurvivors.push(sp);
                else
                {
                    if (sp.parent != null)
                        sp.parent.removeChild(sp);
                    sp.dispose();
                }
            }
            _splashes = splashSurvivors;

            return _items.length + _splashes.length;
        }
    }
}

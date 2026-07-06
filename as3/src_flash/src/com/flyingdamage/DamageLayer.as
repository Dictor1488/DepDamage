package com.flyingdamage
{
    import flash.display.Sprite;

    public class DamageLayer extends Sprite
    {
        private var _app:FlyingDamageApp;
        private var _items:Vector.<FloatingNumber>;

        public function DamageLayer(app:FlyingDamageApp)
        {
            _app = app;
            _items = new Vector.<FloatingNumber>();
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function showDamage(vehicleID:String, damage:int,
                                   colorRGB:uint, fontSize:int, alpha:Number):void
        {
            if (damage <= 0)
                return;
            var fn:FloatingNumber = new FloatingNumber(vehicleID, damage, colorRGB, fontSize, alpha);
            addChild(fn);
            _items.push(fn);
            try { _app.debugLog("DamageLayer showDamage vid=" + vehicleID + " dmg=" + damage + " items=" + _items.length); } catch (e:Error) {}
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

        // Called each frame by the app; returns number of active items.
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
            return _items.length;
        }
    }
}

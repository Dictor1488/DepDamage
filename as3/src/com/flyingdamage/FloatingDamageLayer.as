package com.flyingdamage
{
    import flash.display.Sprite;
    import flash.utils.Dictionary;

    public final class FloatingDamageLayer extends Sprite
    {
        private var _numbers:Dictionary = new Dictionary();

        public function FloatingDamageLayer()
        {
            mouseEnabled = false;
            mouseChildren = false;
        }

        public function createDamage(id:int, damage:int, damageFlag:int):void
        {
            removeDamage(id);
            if (damage <= 0)
                return;

            var mc:FloatingDamageNumber = new FloatingDamageNumber(
                formatDamage(damage, damageFlag),
                damage
            );
            mc.visible = false;
            addChild(mc);
            _numbers[id] = mc;
        }

        public function updateDamage(id:int, xPos:Number, yPos:Number, alphaValue:Number, isVisible:Boolean):void
        {
            var mc:FloatingDamageNumber = _numbers[id] as FloatingDamageNumber;
            if (mc)
                mc.updateScreenPosition(xPos, yPos, alphaValue, isVisible);
        }

        public function removeDamage(id:int):void
        {
            var mc:FloatingDamageNumber = _numbers[id] as FloatingDamageNumber;
            if (!mc)
                return;
            mc.dispose();
            delete _numbers[id];
        }

        private function formatDamage(value:int, damageFlag:int):String
        {
            var color:String = '#FFFFFF';
            if (damageFlag == 1)
                color = '#FFDD66';
            else if (damageFlag == 2)
                color = '#99CCFF';
            else if (damageFlag == 3)
                color = '#99FF99';
            else if (damageFlag == 4)
                color = '#FF6666';
            return '<font color="' + color + '">-' + value.toString() + '</font>';
        }
    }
}

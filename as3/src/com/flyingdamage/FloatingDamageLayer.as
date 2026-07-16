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

        public function createDamage(id:int, damage:int, damageFlag:int,
                                     playerColor:String, allyColor:String,
                                     enemyColor:String, fontSize:int):void
        {
            removeDamage(id);
            if (damage <= 0)
                return;

            var color:String = 'FFFFFF';
            if (damageFlag == 1)
                color = playerColor;
            else if (damageFlag == 2 || damageFlag == 3)
                color = allyColor;
            else if (damageFlag == 4)
                color = enemyColor;

            var mc:FloatingDamageNumber = new FloatingDamageNumber(
                '-' + damage.toString(),
                damage,
                color,
                fontSize
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
    }
}

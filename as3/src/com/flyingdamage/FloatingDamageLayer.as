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
                                     enemyColor:String, allyFireColor:String,
                                     enemyFireColor:String, fontSize:int):void
        {
            removeDamage(id);
            if (damage <= 0)
                return;

            var isFire:Boolean = damageFlag >= 10;
            var sourceFlag:int = isFire ? damageFlag - 10 : damageFlag;
            var color:String = 'FFFFFF';

            // The flag describes who caused the hit, so translate it to the
            // damaged target side. Player/allied source damages an enemy;
            // enemy source damages an ally.
            if (isFire)
            {
                if (sourceFlag == 1 || sourceFlag == 2 || sourceFlag == 3)
                    color = enemyFireColor;
                else if (sourceFlag == 4)
                    color = allyFireColor;
            }
            else
            {
                if (sourceFlag == 1)
                    color = playerColor;
                else if (sourceFlag == 2 || sourceFlag == 3)
                    color = enemyColor;
                else if (sourceFlag == 4)
                    color = allyColor;
            }

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

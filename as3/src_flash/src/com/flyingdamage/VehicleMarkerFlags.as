package com.flyingdamage
{
    public class VehicleMarkerFlags
    {
        public static const DAMAGE_NONE:String = "none";
        public static const DAMAGE_SHOT:String = "shot";
        public static const DAMAGE_FIRE:String = "fire";
        public static const DAMAGE_RAMMING:String = "ramming";
        public static const DAMAGE_WORLD_COLLISION:String = "world_collision";
        public static const DAMAGE_DEATH_ZONE:String = "death_zone";
        public static const DAMAGE_DROWNING:String = "drowning";
        public static const DAMAGE_EXPLOSION:String = "explosion";
        public static const DAMAGE_BLOCKED:String = "blocked";
        public static const DAMAGE_BLOCKED_CRIT:String = "blocked_crit";
        public static const DAMAGE_RICOCHET:String = "ricochet";

        public static const DAMAGE_FROM_OTHER_FLAG:uint = 0;
        public static const DAMAGE_FROM_SQUAD_FLAG:uint = 1;
        public static const DAMAGE_FROM_PLAYER_FLAG:uint = 2;

        public static const ALL_DAMAGE_TYPES:Array = [DAMAGE_SHOT, DAMAGE_FIRE, DAMAGE_RAMMING, DAMAGE_WORLD_COLLISION, DAMAGE_DEATH_ZONE, DAMAGE_DROWNING, DAMAGE_EXPLOSION];
        public static const ALLOWED_DAMAGE_TYPES:Array = [DAMAGE_SHOT, DAMAGE_FIRE, DAMAGE_RAMMING, DAMAGE_WORLD_COLLISION, DAMAGE_DEATH_ZONE, DAMAGE_DROWNING, DAMAGE_EXPLOSION];
        public static const LABELED_DAMAGE_TYPES:Array = [DAMAGE_BLOCKED, DAMAGE_BLOCKED_CRIT, DAMAGE_RICOCHET];

        public static function checkLabeledDamages(damageType:String):Boolean
        {
            return damageType != null && damageType != "" && LABELED_DAMAGE_TYPES.indexOf(damageType) != -1;
        }

        public static function checkAllowedDamages(damageType:String):Boolean
        {
            if (damageType == null || damageType == "")
                return true;
            return ALLOWED_DAMAGE_TYPES.indexOf(damageType) != -1 || LABELED_DAMAGE_TYPES.indexOf(damageType) != -1;
        }

        public static function getDamageColorName(source:uint, markerColor:String = "red"):String
        {
            if (source == DAMAGE_FROM_PLAYER_FLAG)
                return "gold";
            if (source == DAMAGE_FROM_SQUAD_FLAG)
                return markerColor == "yellow" || markerColor == "purple" ? "yellow" : "orange";
            if (markerColor == "red") return "red";
            if (markerColor == "purple") return "purple";
            return "green";
        }

        public static function getColorRGB(colorName:String):uint
        {
            switch (colorName)
            {
                case "gold": return 0xFFDC3C;
                case "orange": return 0xFF9A2E;
                case "yellow": return 0xFFE94A;
                case "green": return 0x7CFF4C;
                case "red": return 0xFF4C4C;
                case "blue": return 0x4CC8FF;
                case "purple": return 0xD979FF;
                case "white": return 0xFFFFFF;
            }
            return 0xFFFFFF;
        }
    }
}

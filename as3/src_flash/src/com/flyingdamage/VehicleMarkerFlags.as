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

        // Ported from the working VehicleMarkerFlags.as. These maps are the
        // original source->marker color rules used by VehicleMarker.getDamageColor().
        public static const PLAYER_DAMAGE_COLOR:Object = {
            "green":"gold",
            "red":"gold",
            "gold":"gold",
            "blue":"gold",
            "yellow":"gold",
            "purple":"gold"
        };

        public static const SQUAD_DAMAGE_COLOR:Object = {
            "green":"orange",
            "red":"orange",
            "gold":"orange",
            "blue":"orange",
            "yellow":"yellow",
            "purple":"yellow"
        };

        public static const OTHER_DAMAGE_COLOR:Object = {
            "green":"green",
            "red":"red",
            "gold":"green",
            "blue":"green",
            "yellow":"green",
            "purple":"purple"
        };

        public static const ALL_DAMAGE_TYPES:Array = [
            DAMAGE_SHOT,
            DAMAGE_FIRE,
            DAMAGE_RAMMING,
            DAMAGE_WORLD_COLLISION,
            DAMAGE_DEATH_ZONE,
            DAMAGE_DROWNING,
            DAMAGE_EXPLOSION
        ];

        // Original WoT marker uses this list for hit-explosion effects, not for
        // regular floating numbers. Keep it separate so shot labels are not hidden.
        public static const ALLOWED_DAMAGE_TYPES:Array = [DAMAGE_FIRE, DAMAGE_EXPLOSION];
        public static const LABELED_DAMAGE_TYPES:Array = [DAMAGE_BLOCKED, DAMAGE_BLOCKED_CRIT, DAMAGE_RICOCHET];
        public static const DAMAGE_FROM_COLORS:Array = [OTHER_DAMAGE_COLOR, SQUAD_DAMAGE_COLOR, PLAYER_DAMAGE_COLOR];

        public static function checkLabeledDamages(damageType:String):Boolean
        {
            return damageType == "" ? true : LABELED_DAMAGE_TYPES.indexOf(damageType) != -1;
        }

        public static function checkAllowedDamages(damageType:String):Boolean
        {
            return damageType == "" ? true : ALLOWED_DAMAGE_TYPES.indexOf(damageType) != -1;
        }

        public static function checkAllowedDamageLabel(damageType:String):Boolean
        {
            if (damageType == null || damageType == "")
                return true;
            return ALL_DAMAGE_TYPES.indexOf(damageType) != -1 || LABELED_DAMAGE_TYPES.indexOf(damageType) != -1;
        }

        public static function getDamageColorName(source:uint, markerColor:String = "red"):String
        {
            if (source > DAMAGE_FROM_PLAYER_FLAG)
                source = DAMAGE_FROM_OTHER_FLAG;
            if (markerColor == null || markerColor == "")
                markerColor = "red";
            var map:Object = DAMAGE_FROM_COLORS[source];
            if (map != null && map.hasOwnProperty(markerColor))
                return String(map[markerColor]);
            return "white";
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

        public static function getColorNameFromRGB(color:uint):String
        {
            color &= 0xFFFFFF;
            var r:int = (color >> 16) & 0xFF;
            var g:int = (color >> 8) & 0xFF;
            var b:int = color & 0xFF;
            if (r > 220 && g > 190 && b < 110) return "gold";
            if (r > 210 && g > 110 && g < 205 && b < 120) return "orange";
            if (r > 200 && g < 135 && b < 135) return "red";
            if (g > 170 && r < 170) return "green";
            if (b > 160 && r < 170) return "blue";
            if (r > 160 && b > 150) return "purple";
            return "red";
        }

        public static function formatDamageValue(value:int):String
        {
            if (value > 0)
                return "-" + String(value);
            if (value < 0)
                return "+" + String(Math.abs(value));
            return "";
        }
    }
}

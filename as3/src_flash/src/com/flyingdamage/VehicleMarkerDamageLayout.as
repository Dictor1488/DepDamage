package com.flyingdamage
{
    public class VehicleMarkerDamageLayout
    {
        public static const DAMAGE_X:Number = -15.0;
        public static const BASE_DAMAGE_Y:Number = -54.0;
        public static const PLAYER_NAME_Y:Number = -12.0;
        public static const VEHICLE_NAME_Y:Number = -12.0;
        public static const LEVEL_ICON_Y:Number = -9.0;
        public static const VEHICLE_ICON_Y:Number = -9.0;

        public static function getDamageLabelOffset(playerNameVisible:Boolean = true, vehicleNameVisible:Boolean = true, levelIconVisible:Boolean = true, vehicleIconVisible:Boolean = true):Number
        {
            var y:Number = BASE_DAMAGE_Y;
            if (playerNameVisible)
                y += PLAYER_NAME_Y;
            if (vehicleNameVisible)
                y += VEHICLE_NAME_Y;
            if (levelIconVisible)
                y += LEVEL_ICON_Y;
            if (vehicleIconVisible)
                y += VEHICLE_ICON_Y;
            return y;
        }
    }
}

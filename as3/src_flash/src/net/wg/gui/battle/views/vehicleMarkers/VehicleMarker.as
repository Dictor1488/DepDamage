package net.wg.gui.battle.views.vehicleMarkers
{
    import flash.display.MovieClip;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import net.wg.gui.battle.views.vehicleMarkers.VO.VehicleMarkerFlags;

    /**
     * Compact VehicleMarker damage implementation.
     * Only the damage-number logic from the provided source is kept here.
     */
    public class VehicleMarker extends MovieClip
    {
        private static const DEFAULT_DAMAGE_COLOR:String = "white";

        public var damage:MovieClip;
        public var playerNameField:TextField;
        public var vehicleNameField:TextField;
        public var levelIcon:MovieClip;
        public var vehicleIcon:MovieClip;
        public var healthBar:Object;
        public var hpField:TextField;

        public var playerHitLabel:Object;
        public var otherHitLabel:Object;

        private var _currHealth:int = -1;
        private var _maxHealth:int = 0;
        private var _markerColor:String = "red";
        private var _isPopulated:Boolean = true;
        private var _damageAnimState:Boolean = true;
        private var _isObserver:Boolean = false;
        private var _damageType:String = VehicleMarkerFlags.DAMAGE_SHOT;

        public function VehicleMarker()
        {
            super();
            if(damage == null)
            {
                damage = new MovieClip();
                addChild(damage);
            }
            ensureLabelSources();
        }

        public function setHealth(value:int) : void
        {
            if(value < 0)
            {
                value = 0;
            }
            _currHealth = value;
            if(healthBar != null)
            {
                try
                {
                    healthBar.currHealth = value;
                }
                catch(e:Error)
                {
                }
            }
            if(hpField != null)
            {
                hpField.text = String(value);
            }
        }

        public function updateHealth(newHealth:int, damageFrom:uint, damageType:String, maxHealth:int = -1) : void
        {
            _damageType = damageType;
            if(newHealth < 0)
            {
                _damageType = VehicleMarkerFlags.DAMAGE_EXPLOSION;
                newHealth = 0;
            }
            if(maxHealth > 0)
            {
                _maxHealth = maxHealth;
            }

            var oldHealth:int = _currHealth >= 0 ? _currHealth : newHealth;
            var delta:int = oldHealth - newHealth;
            _currHealth = newHealth;

            var colorName:String = getDamageColor(damageFrom);
            if(healthBar != null)
            {
                try
                {
                    if("updateHealth" in healthBar)
                    {
                        healthBar.updateHealth(newHealth, colorName);
                    }
                    else
                    {
                        healthBar.currHealth = newHealth;
                    }
                }
                catch(e:Error)
                {
                }
            }
            if(hpField != null)
            {
                hpField.text = String(newHealth);
            }

            var text:String = "";
            if(delta < 0)
            {
                text = "+" + int(Math.abs(delta));
            }
            else if(delta > 0)
            {
                text = "-" + delta;
            }

            if(text != "")
            {
                addDamageLabel(damageFrom, text);
            }
        }

        public function setVehicleInfo(vehicleName:String, playerName:String = "", markerColor:String = "red", maxHealth:int = 0) : void
        {
            if(vehicleNameField != null)
            {
                vehicleNameField.text = vehicleName;
            }
            if(playerNameField != null)
            {
                playerNameField.text = playerName;
            }
            if(markerColor != null && markerColor != "")
            {
                _markerColor = markerColor;
            }
            if(maxHealth > 0)
            {
                _maxHealth = maxHealth;
            }
        }

        public function updateState(markerColor:String, isObserver:Boolean = false, damageType:String = "") : void
        {
            if(markerColor != null && markerColor != "")
            {
                _markerColor = markerColor;
            }
            _isObserver = isObserver;
            if(damageType != null && damageType != "")
            {
                _damageType = damageType;
            }
        }

        public function applyExtensionParams(params:Object) : void
        {
            if(params == null)
            {
                return;
            }
            try
            {
                if(params.damagaLabelsExtended && params.damagaLabelsExtended.hasOwnProperty("enabled"))
                {
                    _damageAnimState = Boolean(params.damagaLabelsExtended.enabled);
                }
            }
            catch(e:Error)
            {
            }
        }

        private function ensureLabelSources() : void
        {
            if(playerHitLabel == null)
            {
                playerHitLabel = { damageLabel: new DamageLabel() };
            }
            if(otherHitLabel == null)
            {
                otherHitLabel = { damageLabel: new DamageLabel() };
            }
        }

        private function addDamageLabel(damageFrom:*, text:*) : void
        {
            if(!_damageAnimState || _isObserver || !_isPopulated)
            {
                return;
            }
            ensureLabelSources();

            var source:Object = damageFrom ? playerHitLabel : otherHitLabel;
            var label:DamageLabel = source.damageLabel as DamageLabel;
            var colorField:TextField = label.showTF(getDamageColor(uint(damageFrom)));
            var format:TextFormat = colorField.getTextFormat();

            damage.x = -15;
            damage.y = getDamageLabelOffset();

            var mc:MovieClip = new MovieClip();
            var tf:TextField = new TextField();
            damage.addChild(mc);
            mc.addChild(tf);

            tf.mouseEnabled = false;
            tf.selectable = false;
            tf.antiAliasType = "advanced";
            tf.width = 54;
            tf.height = 28;
            tf.defaultTextFormat = format;
            tf.setTextFormat(format);
            tf.filters = colorField.filters;
            tf.text = String(text);

            new DamageAnimatedLabel(mc, 40);
        }

        private function getDamageLabelOffset() : Number
        {
            var y:Number = -54;
            if(playerNameField != null && playerNameField.visible)
            {
                y -= 12;
            }
            if(vehicleNameField != null && vehicleNameField.visible)
            {
                y -= 12;
            }
            if(levelIcon != null && levelIcon.visible)
            {
                y -= 9;
            }
            if(vehicleIcon != null && vehicleIcon.visible)
            {
                y -= 9;
            }
            return y;
        }

        private function getDamageColor(damageFrom:uint) : String
        {
            if(_isObserver)
            {
                return DEFAULT_DAMAGE_COLOR;
            }
            if(damageFrom >= VehicleMarkerFlags.DAMAGE_FROM_COLORS.length)
            {
                damageFrom = VehicleMarkerFlags.DAMAGE_FROM_OTHER_FLAG;
            }
            var map:Object = VehicleMarkerFlags.DAMAGE_FROM_COLORS[damageFrom];
            var result:String = map[_markerColor];
            return result != null ? result : DEFAULT_DAMAGE_COLOR;
        }
    }
}

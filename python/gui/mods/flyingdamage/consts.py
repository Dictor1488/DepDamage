# -*- coding: utf-8 -*-

# Local damage origin flags. The AS3 side can map these to colors/messages.
FROM_UNKNOWN = 0
FROM_PLAYER = 1
FROM_SQUAD = 2
FROM_ALLY = 3
FROM_ENEMY = 4

# Packed into the damageType string in the same spirit as XVM:
# "attackReason,attackerVehicleID".
PACK_SEPARATOR = ','

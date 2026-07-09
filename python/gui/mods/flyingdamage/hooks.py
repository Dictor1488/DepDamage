# -*- coding: utf-8 -*-
"""XVM-like hook layer.

The important idea is copied from the XVM flow:
VehicleMarkerPlugin._updateVehicleHealth is intercepted, attacker info is packed
into the marker updateHealth call, and AS3 does the visual work.
"""

import logging

from constants import ATTACK_REASONS
from BattleReplay import g_replayCtrl
from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider
from gui.battle_control.battle_constants import PLAYER_GUI_PROPS

from xfw import overrideMethod

from flyingdamage.consts import FROM_UNKNOWN, FROM_PLAYER, FROM_SQUAD, FROM_ALLY, FROM_ENEMY, PACK_SEPARATOR

LOG = logging.getLogger('DepDamage')
_ENABLED = False


def _safe_attack_reason(attackReasonID):
    try:
        return ATTACK_REASONS[attackReasonID]
    except Exception:
        return 'unknown'


class _DamageOrigin(object):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.playerVehicleID = 0

    def update_player_vehicle_id(self):
        try:
            self.playerVehicleID = self.sessionProvider.getArenaDP().getPlayerVehicleID()
        except Exception:
            self.playerVehicleID = 0

    def get_damage_flag(self, attackerInfo):
        if not attackerInfo:
            return FROM_UNKNOWN
        attackerID = attackerInfo.vehicleID
        if not self.playerVehicleID:
            self.update_player_vehicle_id()
        if attackerID == self.playerVehicleID:
            return FROM_PLAYER
        try:
            props = self.sessionProvider.getCtx().getPlayerGuiProps(attackerID, attackerInfo.team)
        except Exception:
            return FROM_UNKNOWN
        if props == PLAYER_GUI_PROPS.squadman:
            return FROM_SQUAD
        if props == PLAYER_GUI_PROPS.ally:
            return FROM_ALLY
        if props == PLAYER_GUI_PROPS.enemy:
            return FROM_ENEMY
        return FROM_UNKNOWN


_ORIGIN = _DamageOrigin()


def _VehicleMarkerPlugin_updateVehicleHealth(base, self, vehicleID, handle, newHealth, aInfo, attackReasonID):
    if not _ENABLED:
        return base(self, vehicleID, handle, newHealth, aInfo, attackReasonID)

    try:
        if g_replayCtrl.isPlaying and g_replayCtrl.isTimeWarpInProgress:
            return base(self, vehicleID, handle, newHealth, aInfo, attackReasonID)

        attackerID = aInfo.vehicleID if aInfo else 0
        damageFlag = _ORIGIN.get_damage_flag(aInfo)
        packedDamageType = PACK_SEPARATOR.join([_safe_attack_reason(attackReasonID), str(attackerID)])

        # This is the XVM-style bridge point. The custom marker SWF must override
        # updateHealth and unpack damageType into real damage type + attackerID.
        self._invokeMarker(handle, 'updateHealth', newHealth, damageFlag, packedDamageType)
        return
    except Exception:
        LOG.exception('[DepDamage] updateVehicleHealth hook failed')
        return base(self, vehicleID, handle, newHealth, aInfo, attackReasonID)


def init():
    global _ENABLED
    _ENABLED = True
    _ORIGIN.update_player_vehicle_id()
    LOG.info('[DepDamage] hooks enabled')


def fini():
    global _ENABLED
    _ENABLED = False
    LOG.info('[DepDamage] hooks disabled')


overrideMethod(VehicleMarkerPlugin, '_updateVehicleHealth')(_VehicleMarkerPlugin_updateVehicleHealth)

# -*- coding: utf-8 -*-
"""Standalone XVM-like hook layer.

No XFW dependency.

Flow:
- replace stock VehicleMarker symbol with DepDamageVehicleMarker;
- intercept VehicleMarkerPlugin._updateVehicleHealth;
- pass packed damage type and attacker id to marker.updateHealth;
- AS3 marker calculates damage delta and renders floating text.
"""

import logging

from BattleReplay import g_replayCtrl
from constants import ATTACK_REASONS
from gui.Scaleform.daapi.view.battle.shared.markers2d.manager import MarkersManager
from gui.Scaleform.daapi.view.battle.shared.markers2d.settings import CommonMarkerType
from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin
from gui.battle_control.battle_constants import PLAYER_GUI_PROPS
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from flyingdamage.consts import (
    FROM_UNKNOWN,
    FROM_PLAYER,
    FROM_SQUAD,
    FROM_ALLY,
    FROM_ENEMY,
    PACK_SEPARATOR,
    STOCK_VEHICLE_MARKER_SYMBOL,
    DEPDAMAGE_VEHICLE_MARKER_SYMBOL,
)

LOG = logging.getLogger('DepDamage')
_ENABLED = False
_PATCHED = False
_ORIGINAL_CREATE_MARKER = None
_ORIGINAL_UPDATE_HEALTH = None


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


def _create_marker_hook(self, symbol, matrixProvider=None, active=True, markerType=CommonMarkerType.NORMAL):
    if _ENABLED and symbol == STOCK_VEHICLE_MARKER_SYMBOL:
        symbol = DEPDAMAGE_VEHICLE_MARKER_SYMBOL
    return _ORIGINAL_CREATE_MARKER(self, symbol, matrixProvider, active, markerType)


def _update_vehicle_health_hook(self, vehicleID, handle, newHealth, aInfo, attackReasonID):
    if not _ENABLED:
        return _ORIGINAL_UPDATE_HEALTH(self, vehicleID, handle, newHealth, aInfo, attackReasonID)

    try:
        if g_replayCtrl.isPlaying and g_replayCtrl.isTimeWarpInProgress:
            return _ORIGINAL_UPDATE_HEALTH(self, vehicleID, handle, newHealth, aInfo, attackReasonID)

        attackerID = aInfo.vehicleID if aInfo else 0
        damageFlag = _ORIGIN.get_damage_flag(aInfo)
        packedDamageType = PACK_SEPARATOR.join([_safe_attack_reason(attackReasonID), str(attackerID)])

        self._invokeMarker(handle, 'updateHealth', newHealth, damageFlag, packedDamageType)
        return
    except Exception:
        LOG.exception('[DepDamage] updateVehicleHealth hook failed')
        return _ORIGINAL_UPDATE_HEALTH(self, vehicleID, handle, newHealth, aInfo, attackReasonID)


def _patch():
    global _PATCHED, _ORIGINAL_CREATE_MARKER, _ORIGINAL_UPDATE_HEALTH
    if _PATCHED:
        return
    _ORIGINAL_CREATE_MARKER = MarkersManager.createMarker
    _ORIGINAL_UPDATE_HEALTH = VehicleMarkerPlugin._updateVehicleHealth
    MarkersManager.createMarker = _create_marker_hook
    VehicleMarkerPlugin._updateVehicleHealth = _update_vehicle_health_hook
    _PATCHED = True
    LOG.info('[DepDamage] standalone hooks patched')


def init():
    global _ENABLED
    _patch()
    _ENABLED = True
    _ORIGIN.update_player_vehicle_id()
    LOG.info('[DepDamage] hooks enabled')


def fini():
    global _ENABLED
    _ENABLED = False
    LOG.info('[DepDamage] hooks disabled')

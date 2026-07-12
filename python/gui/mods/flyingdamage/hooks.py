# -*- coding: utf-8 -*-
"""Standalone floating-damage hooks.

The stock marker application is left untouched.  We only observe vehicle health
updates, project the stock marker position once, and create an independent
screen-space label in DepDamageFlash.swf.
"""

import logging

from BattleReplay import g_replayCtrl
from constants import ATTACK_REASONS
from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin
from gui.battle_control.battle_constants import PLAYER_GUI_PROPS
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from flyingdamage.overlay import DepDamageFlash

FROM_UNKNOWN = 0
FROM_PLAYER = 1
FROM_SQUAD = 2
FROM_ALLY = 3
FROM_ENEMY = 4

LOG = logging.getLogger('DepDamage')
_ENABLED = False
_PATCHED = False
_ORIGINAL_START = None
_ORIGINAL_STOP = None
_ORIGINAL_UPDATE_HEALTH = None
_OVERLAY = None
_LAST_HEALTH = {}


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


def _start_hook(self, *args, **kwargs):
    result = _ORIGINAL_START(self, *args, **kwargs)
    if not _ENABLED:
        return result

    try:
        global _OVERLAY
        if _OVERLAY is None:
            _OVERLAY = DepDamageFlash(self._clazz)
            LOG.info('[DepDamage] screen overlay created')
    except Exception:
        LOG.exception('[DepDamage] failed to create screen overlay')
    return result


def _stop_hook(self, *args, **kwargs):
    try:
        global _OVERLAY
        if _OVERLAY is not None:
            _OVERLAY.close()
            _OVERLAY = None
        _LAST_HEALTH.clear()
    except Exception:
        LOG.exception('[DepDamage] failed to close screen overlay')
    return _ORIGINAL_STOP(self, *args, **kwargs)


def _update_vehicle_health_hook(self, vehicleID, handle, newHealth, aInfo, attackReasonID, *args, **kwargs):
    oldHealth = _LAST_HEALTH.get(vehicleID)
    _LAST_HEALTH[vehicleID] = newHealth

    result = _ORIGINAL_UPDATE_HEALTH(
        self, vehicleID, handle, newHealth, aInfo, attackReasonID, *args, **kwargs
    )

    if not _ENABLED or oldHealth is None:
        return result

    try:
        if g_replayCtrl.isPlaying and g_replayCtrl.isTimeWarpInProgress:
            return result

        damage = int(oldHealth - max(newHealth, 0))
        if damage <= 0 or _OVERLAY is None:
            return result

        attackerID = aInfo.vehicleID if aInfo else 0
        damageFlag = _ORIGIN.get_damage_flag(aInfo)
        damageType = _safe_attack_reason(attackReasonID)
        _OVERLAY.showDamage(vehicleID, damage, attackerID, damageType, damageFlag)
    except Exception:
        LOG.exception('[DepDamage] updateVehicleHealth overlay hook failed')

    return result


def _patch():
    global _PATCHED, _ORIGINAL_START, _ORIGINAL_STOP, _ORIGINAL_UPDATE_HEALTH
    if _PATCHED:
        return

    _ORIGINAL_START = VehicleMarkerPlugin.start
    _ORIGINAL_STOP = VehicleMarkerPlugin.stop
    _ORIGINAL_UPDATE_HEALTH = VehicleMarkerPlugin._updateVehicleHealth

    VehicleMarkerPlugin.start = _start_hook
    VehicleMarkerPlugin.stop = _stop_hook
    VehicleMarkerPlugin._updateVehicleHealth = _update_vehicle_health_hook

    _PATCHED = True
    LOG.info('[DepDamage] standalone overlay hooks patched')


def init():
    global _ENABLED
    _patch()
    _ENABLED = True
    _ORIGIN.update_player_vehicle_id()
    LOG.info('[DepDamage] hooks enabled')


def fini():
    global _ENABLED, _OVERLAY
    _ENABLED = False
    try:
        if _OVERLAY is not None:
            _OVERLAY.close()
            _OVERLAY = None
    except Exception:
        LOG.exception('[DepDamage] overlay close failed during fini')
    _LAST_HEALTH.clear()
    LOG.info('[DepDamage] hooks disabled')

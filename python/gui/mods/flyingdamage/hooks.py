# -*- coding: utf-8 -*-
"""Standalone floating-damage hooks and screen overlay runtime."""

import logging

import BigWorld
import GUI
import Math
import SCALEFORM

from BattleReplay import g_replayCtrl
from constants import ATTACK_REASONS
from gui import DEPTH_OF_VehicleMarker
from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin
from gui.Scaleform.daapi.view.external_components import ExternalFlashComponent, ExternalFlashSettings
from gui.Scaleform.flash_wrapper import InputKeyMode
from gui.Scaleform.framework.entities.BaseDAAPIModule import BaseDAAPIModule
from gui.battle_control.battle_constants import PLAYER_GUI_PROPS
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

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
_ORIGINAL_SET_HEALTH = None
_ORIGINAL_UPDATE_HEALTH = None
_OVERLAY = None
_LAST_HEALTH = {}


class DepDamageFlashMeta(BaseDAAPIModule):

    def as_showDamage(self, screenWidth, screenHeight, x, y, damage, attackerID, damageType, damageFlag):
        if self._isDAAPIInited():
            return self.flashObject.as_showDamage(
                screenWidth, screenHeight, x, y, damage, attackerID, damageType, damageFlag
            )


class DepDamageFlash(ExternalFlashComponent, DepDamageFlashMeta):

    def __init__(self, vehicleMarkerClass):
        super(DepDamageFlash, self).__init__(
            ExternalFlashSettings('DepDamageFlash', 'DepDamageFlash.swf', 'root', None)
        )
        self._vehicleMarkerClass = vehicleMarkerClass
        self._viewProjection = Math.Matrix()
        self._tempMatrix = Math.Matrix()

        self.createExternalComponent()
        self.movie.backgroundAlpha = 0.0
        self.movie.scaleMode = SCALEFORM.eMovieScaleMode.NO_SCALE
        self.component.wg_inputKeyMode = InputKeyMode.NO_HANDLE
        self.component.position.z = DEPTH_OF_VehicleMarker - 0.01
        self.component.focus = False
        self.component.moveFocus = False
        self.active(True)

    def showDamage(self, vehicleID, damage, attackerID, damageType, damageFlag):
        try:
            vehicle = BigWorld.entity(vehicleID)
            if vehicle is None or not getattr(vehicle, 'isStarted', False):
                return False

            provider = self._vehicleMarkerClass.fetchMatrixProvider(vehicle)
            self._tempMatrix.set(provider)
            point = self._tempMatrix.translation
            projected, visible = self._projectPoint(point)
            if not visible:
                return False

            screenWidth, screenHeight = GUI.screenResolution()
            x = (0.5 + 0.5 * projected.x) * screenWidth
            y = (0.5 - 0.5 * projected.y) * screenHeight
            self.as_showDamage(
                screenWidth, screenHeight, x, y,
                int(damage), attackerID, damageType, int(damageFlag)
            )
            return True
        except Exception:
            LOG.exception('[DepDamage] failed to project/show damage')
            return False

    def _projectPoint(self, point):
        camera = BigWorld.camera()
        if camera is None:
            return Math.Vector4(), False

        projection = BigWorld.projection()
        self._viewProjection.perspectiveProjection(
            projection.fov,
            BigWorld.getAspectRatio(),
            projection.nearPlane,
            projection.farPlane
        )
        self._viewProjection.preMultiply(camera.matrix)

        clip = Math.Vector4(point.x, point.y, point.z, 1)
        clip = self._viewProjection.applyV4Point(clip)
        visible = (
            point.lengthSquared != 0.0 and
            clip.w > 0 and
            -1 <= clip.x / clip.w <= 1 and
            -1 <= clip.y / clip.w <= 1
        )
        if clip.w != 0:
            clip = clip.scale(1.0 / clip.w)
        return clip, visible


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


def _set_health_marker_hook(self, vehicleID, handle, newHealth, *args, **kwargs):
    _LAST_HEALTH[vehicleID] = max(int(newHealth), 0)
    return _ORIGINAL_SET_HEALTH(self, vehicleID, handle, newHealth, *args, **kwargs)


def _update_vehicle_health_hook(self, vehicleID, handle, newHealth, aInfo, attackReasonID, *args, **kwargs):
    normalizedHealth = max(int(newHealth), 0)
    oldHealth = _LAST_HEALTH.get(vehicleID)

    result = _ORIGINAL_UPDATE_HEALTH(
        self, vehicleID, handle, newHealth, aInfo, attackReasonID, *args, **kwargs
    )
    _LAST_HEALTH[vehicleID] = normalizedHealth

    if not _ENABLED or oldHealth is None:
        return result

    try:
        if g_replayCtrl.isPlaying and g_replayCtrl.isTimeWarpInProgress:
            return result

        damage = oldHealth - normalizedHealth
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
    global _PATCHED, _ORIGINAL_START, _ORIGINAL_STOP
    global _ORIGINAL_SET_HEALTH, _ORIGINAL_UPDATE_HEALTH
    if _PATCHED:
        return

    _ORIGINAL_START = VehicleMarkerPlugin.start
    _ORIGINAL_STOP = VehicleMarkerPlugin.stop
    _ORIGINAL_SET_HEALTH = VehicleMarkerPlugin._setHealthMarker
    _ORIGINAL_UPDATE_HEALTH = VehicleMarkerPlugin._updateVehicleHealth

    VehicleMarkerPlugin.start = _start_hook
    VehicleMarkerPlugin.stop = _stop_hook
    VehicleMarkerPlugin._setHealthMarker = _set_health_marker_hook
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

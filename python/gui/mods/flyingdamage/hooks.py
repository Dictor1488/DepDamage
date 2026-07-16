# -*- coding: utf-8 -*-
"""Floating damage hooks with frozen world motion and Flash text styling."""

import logging

import BigWorld
import GUI
import Math
import SCALEFORM
import constants

from BattleReplay import g_replayCtrl
from constants import ATTACK_REASONS
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

    def as_configureScreen(self, screenWidth, screenHeight):
        if self._isDAAPIInited():
            return self.flashObject.as_configureScreen(screenWidth, screenHeight)

    def as_createDamage(self, numberID, damage, damageFlag):
        if self._isDAAPIInited():
            return self.flashObject.as_createDamage(numberID, damage, damageFlag)

    def as_updateDamage(self, numberID, x, y, alpha, visible):
        if self._isDAAPIInited():
            return self.flashObject.as_updateDamage(numberID, x, y, alpha, visible)

    def as_removeDamage(self, numberID):
        if self._isDAAPIInited():
            return self.flashObject.as_removeDamage(numberID)


class _FlashDamageNumber(object):
    DURATION = 2.0
    WORLD_RISE = 1.45
    TICK = 0.025

    def __init__(self, numberID, worldPoint, damage, damageFlag, overlay, projector, onDispose):
        self._numberID = int(numberID)
        self._worldPoint = Math.Vector3(worldPoint.x, worldPoint.y, worldPoint.z)
        self._startTime = BigWorld.time()
        self._overlay = overlay
        self._projector = projector
        self._callbackID = None
        self._disposed = False
        self._onDispose = onDispose

        self._overlay.createLabel(self._numberID, int(damage), int(damageFlag))
        self._tick()

    def _alpha(self, progress):
        if progress > 0.78:
            return max(0.0, 1.0 - (progress - 0.78) / 0.22)
        return 1.0

    def _schedule(self):
        if not self._disposed:
            self._callbackID = BigWorld.callback(self.TICK, self._tick)

    def _tick(self):
        self._callbackID = None
        if self._disposed:
            return

        progress = (BigWorld.time() - self._startTime) / self.DURATION
        if progress >= 1.0:
            self.dispose()
            return

        eased = 1.0 - (1.0 - progress) * (1.0 - progress)
        point = Math.Vector3(
            self._worldPoint.x,
            self._worldPoint.y + self.WORLD_RISE * eased,
            self._worldPoint.z
        )
        projected, visible = self._projector(point)
        if visible:
            screenWidth, screenHeight = GUI.screenResolution()
            x = (0.5 + 0.5 * projected.x) * screenWidth
            y = (0.5 - 0.5 * projected.y) * screenHeight
            self._overlay.updateLabel(self._numberID, x, y, self._alpha(progress), True)
        else:
            self._overlay.updateLabel(self._numberID, 0.0, 0.0, 0.0, False)

        self._schedule()

    def dispose(self):
        if self._disposed:
            return
        self._disposed = True

        if self._callbackID is not None:
            try:
                BigWorld.cancelCallback(self._callbackID)
            except Exception:
                pass
            self._callbackID = None

        if self._overlay is not None:
            self._overlay.removeLabel(self._numberID)

        callback = self._onDispose
        self._onDispose = None
        self._overlay = None
        self._projector = None
        if callback is not None:
            callback(self)


class FlashDamageOverlay(ExternalFlashComponent, DepDamageFlashMeta):
    """Merges hits in Python, projects a frozen world point, and renders in Flash."""

    SPAWN_HEIGHT = 0.75
    MERGE_WINDOW = 0.22

    def __init__(self, vehicleMarkerClass):
        super(FlashDamageOverlay, self).__init__(
            ExternalFlashSettings('DepDamageFlash', 'DepDamageFlash.swf', 'root', None)
        )
        self._vehicleMarkerClass = vehicleMarkerClass
        self._viewProjection = Math.Matrix()
        self._tempMatrix = Math.Matrix()
        self._numbers = set()
        self._pending = {}
        self._nextNumberID = 1
        self._screenWindow = None
        self._configuredResolution = None

        self.createExternalComponent()
        self.movie.backgroundAlpha = 0.0
        self.movie.scaleMode = SCALEFORM.eMovieScaleMode.NO_SCALE
        self.component.wg_inputKeyMode = InputKeyMode.NO_HANDLE
        self.component.focus = False
        self.component.moveFocus = False
        self.component.size = (2.0, 2.0)

        self._screenWindow = GUI.Window()
        self._screenWindow.horizontalAnchor = GUI.Simple.eHAnchor.CENTER
        self._screenWindow.verticalAnchor = GUI.Simple.eVAnchor.CENTER
        self._screenWindow.position = (0.0, 0.0, 0.15)
        self._screenWindow.size = (2.0, 2.0)
        self._screenWindow.visible = True
        self._screenWindow.addChild(self.component)
        GUI.addRoot(self._screenWindow)

        LOG.info('[DepDamage] exact ProTanki Flash shadow overlay created')

    def _configureScreen(self):
        resolution = GUI.screenResolution()
        if resolution != self._configuredResolution:
            self.as_configureScreen(resolution[0], resolution[1])
            self._configuredResolution = resolution

    def createLabel(self, numberID, damage, damageFlag):
        self._configureScreen()
        self.as_createDamage(numberID, damage, damageFlag)

    def updateLabel(self, numberID, x, y, alpha, visible):
        self._configureScreen()
        self.as_updateDamage(numberID, x, y, alpha, visible)

    def removeLabel(self, numberID):
        self.as_removeDamage(numberID)

    def close(self):
        for pending in self._pending.values():
            callbackID = pending.get('callbackID')
            if callbackID is not None:
                try:
                    BigWorld.cancelCallback(callbackID)
                except Exception:
                    pass
        self._pending.clear()

        for number in tuple(self._numbers):
            number.dispose()
        self._numbers.clear()

        try:
            if self._screenWindow is not None:
                try:
                    self._screenWindow.delChild(self.component)
                except Exception:
                    pass
                try:
                    GUI.delRoot(self._screenWindow)
                except Exception:
                    pass
                self._screenWindow = None
        finally:
            super(FlashDamageOverlay, self).close()

    def _removeNumber(self, number):
        self._numbers.discard(number)

    def showDamage(self, vehicleID, damage, attackerID, damageType, damageFlag):
        try:
            vehicle = BigWorld.entity(vehicleID)
            if vehicle is None or not getattr(vehicle, 'isStarted', False):
                return False

            provider = self._vehicleMarkerClass.fetchMatrixProvider(vehicle)
            self._tempMatrix.set(provider)
            markerPoint = self._tempMatrix.translation
            point = Math.Vector3(
                markerPoint.x,
                markerPoint.y + self.SPAWN_HEIGHT,
                markerPoint.z
            )
            _, visible = self._projectPoint(point)
            if not visible:
                return False

            pending = self._pending.get(vehicleID)
            if pending is not None:
                pending['damage'] += int(damage)
                pending['point'] = point
                pending['damageFlag'] = damageFlag
                return True

            callbackID = BigWorld.callback(
                self.MERGE_WINDOW,
                lambda vehicleID=vehicleID: self._flushPending(vehicleID)
            )
            self._pending[vehicleID] = {
                'damage': int(damage),
                'point': point,
                'damageFlag': damageFlag,
                'callbackID': callbackID
            }
            return True
        except Exception:
            LOG.exception('[DepDamage] failed to queue Flash damage number')
            return False

    def _flushPending(self, vehicleID):
        pending = self._pending.pop(vehicleID, None)
        if pending is None:
            return
        try:
            numberID = self._nextNumberID
            self._nextNumberID += 1
            number = _FlashDamageNumber(
                numberID,
                pending['point'],
                pending['damage'],
                pending['damageFlag'],
                self,
                self._projectPoint,
                self._removeNumber
            )
            self._numbers.add(number)
        except Exception:
            LOG.exception('[DepDamage] failed to spawn Flash damage number')

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
            _OVERLAY = FlashDamageOverlay(self._clazz)
    except Exception:
        LOG.exception('[DepDamage] failed to create exact-style Flash overlay')
    return result


def _stop_hook(self, *args, **kwargs):
    try:
        global _OVERLAY
        if _OVERLAY is not None:
            _OVERLAY.close()
            _OVERLAY = None
        _LAST_HEALTH.clear()
    except Exception:
        LOG.exception('[DepDamage] failed to close Flash overlay')
    return _ORIGINAL_STOP(self, *args, **kwargs)


def _set_health_marker_hook(self, vehicleID, handle, newHealth, *args, **kwargs):
    _LAST_HEALTH[vehicleID] = max(int(newHealth), 0)
    return _ORIGINAL_SET_HEALTH(self, vehicleID, handle, newHealth, *args, **kwargs)


def _update_vehicle_health_hook(self, vehicleID, handle, newHealth, aInfo, attackReasonID, *args, **kwargs):
    normalizedHealth = max(int(newHealth), 0)
    oldHealth = _LAST_HEALTH.get(vehicleID)

    markerHealth = newHealth
    isAmmoBayDestroyed = constants.SPECIAL_VEHICLE_HEALTH.IS_AMMO_BAY_DESTROYED(markerHealth)
    if markerHealth < 0 and not isAmmoBayDestroyed:
        markerHealth = 0
    if (self.sessionProvider.shared.vehicleState.isInPostmortem and
            markerHealth < 0 and isAmmoBayDestroyed and not aInfo):
        markerHealth = 0

    self._setHealthMarker(vehicleID, handle, markerHealth)
    _LAST_HEALTH[vehicleID] = normalizedHealth

    if not _ENABLED or oldHealth is None:
        return None

    try:
        if g_replayCtrl.isPlaying and g_replayCtrl.isTimeWarpInProgress:
            return None
        damage = oldHealth - normalizedHealth
        if damage <= 0 or _OVERLAY is None:
            return None

        attackerID = aInfo.vehicleID if aInfo else 0
        damageFlag = _ORIGIN.get_damage_flag(aInfo)
        damageType = _safe_attack_reason(attackReasonID)
        _OVERLAY.showDamage(vehicleID, damage, attackerID, damageType, damageFlag)
    except Exception:
        LOG.exception('[DepDamage] updateVehicleHealth exact-style Flash hook failed')
    return None


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
    LOG.info('[DepDamage] exact ProTanki DropShadowFilter renderer patched')


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
        LOG.exception('[DepDamage] Flash overlay close failed during fini')
    _LAST_HEALTH.clear()
    LOG.info('[DepDamage] hooks disabled')

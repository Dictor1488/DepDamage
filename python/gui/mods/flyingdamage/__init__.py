# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Battle marker-layer renderer for FlyingDamage.
#
# All previous overlay approaches created/logged correctly but were not visible
# for the user. This build renders through the game's own markers2d canvas by
# creating short-lived VehicleMarker symbols bound to world matrices.

import logging

import BigWorld
import Math

from PlayerEvents import g_playerEvents

logger = logging.getLogger(__name__)

_pushLog = [0]
_testLog = [False]
_markerParent = [None]
_markerPlugin = [None]
_markerIDs = set()
_markerHookInstalled = [False]


def _installMarkerLayerHook():
    if _markerHookInstalled[0]:
        return
    try:
        from gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins import VehicleMarkerPlugin
    except Exception:
        logger.error('[FlyingDamage] cannot import VehicleMarkerPlugin', exc_info=True)
        return

    oldStart = VehicleMarkerPlugin.start
    oldStop = VehicleMarkerPlugin.stop

    def newStart(self, *args, **kwargs):
        result = oldStart(self, *args, **kwargs)
        try:
            _markerParent[0] = self._parentObj
            _markerPlugin[0] = self
            logger.info('[FlyingDamage] marker layer captured: %s', _markerParent[0])
        except Exception:
            logger.error('[FlyingDamage] marker layer capture failed', exc_info=True)
        return result

    def newStop(self, *args, **kwargs):
        try:
            if _markerPlugin[0] is self:
                _destroyAllMarkerDamage()
                _markerParent[0] = None
                _markerPlugin[0] = None
                logger.info('[FlyingDamage] marker layer released')
        except Exception:
            logger.error('[FlyingDamage] marker layer release failed', exc_info=True)
        return oldStop(self, *args, **kwargs)

    VehicleMarkerPlugin.start = newStart
    VehicleMarkerPlugin.stop = newStop
    _markerHookInstalled[0] = True
    logger.info('[FlyingDamage] VehicleMarkerPlugin hook installed')


def _destroyMarker(markerID):
    parent = _markerParent[0]
    try:
        if parent is not None:
            parent.destroyMarker(markerID)
    except Exception:
        logger.error('[FlyingDamage] destroy marker failed id=%s', markerID, exc_info=True)
    try:
        _markerIDs.discard(markerID)
    except Exception:
        pass


def _destroyAllMarkerDamage():
    for markerID in list(_markerIDs):
        _destroyMarker(markerID)
    try:
        _markerIDs.clear()
    except Exception:
        pass


def _makeMatrix(x, y, z):
    m = Math.Matrix()
    m.setTranslate(Math.Vector3(float(x), float(y), float(z)))
    return m


def _entityAnchorFromVehicleID(vehicleID):
    try:
        vehicle = BigWorld.entity(int(vehicleID))
        if vehicle is None:
            return None
        pos = getattr(vehicle, 'position', None)
        if pos is None:
            tmp = Math.Matrix()
            tmp.set(vehicle.matrix)
            pos = tmp.translation
        return (float(pos.x), float(pos.y) + 4.5, float(pos.z))
    except Exception:
        return None


def _playerAnchor():
    try:
        player = BigWorld.player()
        vid = getattr(player, 'playerVehicleID', None)
        if vid is None:
            vid = getattr(player, 'vehicleID', None)
        anchor = _entityAnchorFromVehicleID(vid)
        if anchor is not None:
            return anchor
    except Exception:
        pass
    try:
        for entity in BigWorld.entities.values():
            if hasattr(entity, 'isStarted') and getattr(entity, 'isStarted', False):
                pos = getattr(entity, 'position', None)
                if pos is not None:
                    return (float(pos.x), float(pos.y) + 4.5, float(pos.z))
    except Exception:
        pass
    return None


class _MarkerLayerRenderer(object):

    def __init__(self):
        self.enabled = False

    def start(self):
        self.enabled = True
        logger.info('[FlyingDamage] marker-layer renderer started')

    def stop(self):
        self.enabled = False
        _destroyAllMarkerDamage()
        logger.info('[FlyingDamage] marker-layer renderer stopped')

    def showWorld(self, wx, wy, wz, fallbackX, fallbackY, damage, colorRGB,
                  fontSize, alpha, riseMeters, lifeTime):
        if not self.enabled:
            return False
        parent = _markerParent[0]
        if parent is None:
            logger.info('[FlyingDamage] marker layer not ready; cannot show d=%s', int(damage))
            return False
        try:
            from gui.Scaleform.daapi.view.battle.shared.markers2d import settings as markerSettings

            markerID = parent.createMarker(
                markerSettings.MARKER_SYMBOL_NAME.VEHICLE_MARKER,
                matrixProvider=_makeMatrix(wx, wy, wz),
                active=True,
                markerType=markerSettings.CommonMarkerType.VEHICLE)
            _markerIDs.add(markerID)

            txt = str(int(damage))
            maxHP = max(int(damage), 1)
            try:
                parent.setMarkerTextLabelEnabled(markerID, True)
            except Exception:
                pass
            try:
                parent.setMarkerCustomDistanceStr(markerID, txt)
            except Exception:
                pass
            try:
                parent.invokeMarker(markerID, 'setVehicleInfo',
                                    'mediumTank', '', txt, 10,
                                    txt, txt, '', '', maxHP,
                                    'enemy', False, 0, '')
                parent.invokeMarker(markerID, 'setHealth', maxHP)
                parent.invokeMarker(markerID, 'update')
            except Exception:
                logger.error('[FlyingDamage] init temp vehicle marker failed', exc_info=True)

            if _pushLog[0] < 40:
                _pushLog[0] += 1
                logger.info('[FlyingDamage] MARKER_LAYER show d=%s markerID=%s world=(%.2f,%.2f,%.2f)',
                            int(damage), markerID, float(wx), float(wy), float(wz))

            self._animateMarker(markerID, float(wx), float(wy), float(wz),
                                float(riseMeters), max(0.5, float(lifeTime)), BigWorld.time())
            return True
        except Exception:
            logger.error('[FlyingDamage] marker-layer show failed', exc_info=True)
            return False

    def _animateMarker(self, markerID, wx, wy, wz, riseMeters, lifeTime, started):
        parent = _markerParent[0]
        if parent is None or markerID not in _markerIDs:
            return
        try:
            age = BigWorld.time() - started
            if age >= lifeTime:
                _destroyMarker(markerID)
                return
            p = age / lifeTime
            parent.setMarkerMatrix(markerID, _makeMatrix(wx, wy + riseMeters * p, wz))
            BigWorld.callback(0.05, lambda: self._animateMarker(markerID, wx, wy, wz, riseMeters, lifeTime, started))
        except Exception:
            logger.error('[FlyingDamage] marker-layer animate failed id=%s', markerID, exc_info=True)
            _destroyMarker(markerID)


class Controller(object):

    def __init__(self):
        self._enabled = True
        self._battleMode = False
        self._renderer = _MarkerLayerRenderer()

    def init(self):
        logger.info('[FlyingDamage] controller.init begin (vehicle marker layer)')
        _installMarkerLayerHook()
        try:
            from .settings.config import g_config
            g_config.registerSettings()
        except Exception:
            logger.error('[FlyingDamage] settings failed', exc_info=True)

        try:
            from .hooks import installHooks
            installHooks()
        except Exception:
            logger.error('[FlyingDamage] installHooks failed', exc_info=True)

        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamage] early suppression failed', exc_info=True)

        g_playerEvents.onAvatarReady += self._onAvatarReady
        g_playerEvents.onAvatarBecomeNonPlayer += self._onBattleLeave
        logger.info('[FlyingDamage] controller.init done')

    def fini(self):
        logger.info('[FlyingDamage] controller.fini')
        try:
            g_playerEvents.onAvatarReady -= self._onAvatarReady
            g_playerEvents.onAvatarBecomeNonPlayer -= self._onBattleLeave
        except Exception:
            pass
        self._onBattleLeave()
        try:
            from .utils import restore_overrides
            restore_overrides()
        except Exception:
            pass

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        _testLog[0] = False
        logger.info('[FlyingDamage] avatar ready -> marker-layer renderer active')
        self._renderer.start()
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            pass
        # Try several times because VehicleMarkerPlugin may start after avatar ready.
        BigWorld.callback(2.0, self._debugTestDamage)
        BigWorld.callback(5.0, self._debugTestDamage)
        BigWorld.callback(8.0, self._debugTestDamage)
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def _debugTestDamage(self):
        if not self._battleMode or _testLog[0]:
            return
        anchor = _playerAnchor()
        if anchor is None:
            logger.info('[FlyingDamage] marker-layer debug: no player/world anchor yet')
            return
        if _markerParent[0] is None:
            logger.info('[FlyingDamage] marker-layer debug: marker parent not captured yet')
            return
        _testLog[0] = True
        wx, wy, wz = anchor
        logger.info('[FlyingDamage] marker-layer debug test world=(%.2f,%.2f,%.2f)', wx, wy, wz)
        self.showDamageWorld(wx, wy, wz, 0.0, 0.0, 9999, 0x00FFFF, 36, 1.0, 2.0, 5.0)

    def _installSuppressionSafe(self):
        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamage] installSuppression failed', exc_info=True)

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FlyingDamage] battle leave')
        self._battleMode = False
        self._renderer.stop()
        try:
            from .hooks import setView, resetState
            setView(None)
            resetState()
        except Exception:
            pass
        try:
            from .suppress import resetState as suppressReset
            suppressReset()
        except Exception:
            pass

    def showDamageAt(self, x, y, damage, colorRGB, fontSize, alpha, risePixels=55.0, lifeTime=1.6):
        # Screen overlay path is intentionally disabled for this build. We need a
        # real world point so the game marker canvas can render it.
        if _pushLog[0] < 10:
            _pushLog[0] += 1
            logger.info('[FlyingDamage] screen damage ignored by marker-layer renderer d=%s', int(damage))

    def showDamageWorld(self, wx, wy, wz, fallbackX, fallbackY, damage, colorRGB,
                        fontSize, alpha, riseMeters=1.35, lifeTime=1.6):
        if not self._battleMode:
            return
        self._renderer.showWorld(wx, wy, wz, fallbackX, fallbackY, damage, colorRGB,
                                 fontSize, alpha, riseMeters, lifeTime)

    def showDamage(self, x, y, damage, colorRGB, fontSize, alpha):
        self.showDamageAt(x, y, damage, colorRGB, fontSize, alpha)


g_controller = Controller()

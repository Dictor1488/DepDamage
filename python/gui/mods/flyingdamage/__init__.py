# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Existing vehicle marker renderer for FlyingDamage.
#
# This build modifies the already-visible marker of the damaged vehicle for a
# short time. It calls marker methods through VehicleMarkerPlugin wrappers,
# because MarkersManager itself does not expose every helper method.

import logging

import BigWorld

from PlayerEvents import g_playerEvents

logger = logging.getLogger(__name__)

_pushLog = [0]
_testLog = [False]
_markerParent = [None]
_markerPlugin = [None]
_markerHookInstalled = [False]
_restoreCallbacks = {}


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
            logger.info('[FlyingDamage] marker layer captured: %s markers=%s',
                        _markerParent[0], len(getattr(self, '_markers', {})))
        except Exception:
            logger.error('[FlyingDamage] marker layer capture failed', exc_info=True)
        return result

    def newStop(self, *args, **kwargs):
        try:
            if _markerPlugin[0] is self:
                _cancelRestores()
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


def _cancelRestores():
    for cbid in list(_restoreCallbacks.values()):
        try:
            BigWorld.cancelCallback(cbid)
        except Exception:
            pass
    _restoreCallbacks.clear()


def _getExistingMarkerID(vehicleID):
    try:
        plugin = _markerPlugin[0]
        if plugin is None:
            return None
        marker = getattr(plugin, '_markers', {}).get(int(vehicleID))
        if marker is None:
            return None
        return marker.getMarkerID()
    except Exception:
        logger.error('[FlyingDamage] get existing marker failed vid=%s', vehicleID, exc_info=True)
        return None


def _getAnyExistingMarkerID():
    try:
        plugin = _markerPlugin[0]
        if plugin is None:
            return None
        markers = getattr(plugin, '_markers', {})
        for _vid, marker in markers.iteritems():
            return marker.getMarkerID()
    except Exception:
        pass
    return None


def _setTextLabelEnabled(markerID, enabled):
    plugin = _markerPlugin[0]
    if plugin is None:
        return False
    try:
        plugin._setMarkerTextLabelEnabled(markerID, enabled)
        return True
    except Exception:
        logger.info('[FlyingDamage] _setMarkerTextLabelEnabled failed markerID=%s enabled=%s', markerID, enabled, exc_info=True)
        return False


def _setCustomDistanceText(markerID, text):
    plugin = _markerPlugin[0]
    if plugin is None:
        return False
    try:
        plugin._setMarkerCustomDistanceStr(markerID, text)
        return True
    except Exception:
        logger.info('[FlyingDamage] _setMarkerCustomDistanceStr failed markerID=%s text=%s', markerID, text, exc_info=True)
        return False


def _invokeMarker(markerID, function, *args):
    plugin = _markerPlugin[0]
    if plugin is None:
        return False
    try:
        plugin._invokeMarker(markerID, function, *args)
        return True
    except Exception:
        logger.info('[FlyingDamage] _invokeMarker failed markerID=%s fn=%s', markerID, function, exc_info=True)
        return False


class _ExistingMarkerRenderer(object):

    def __init__(self):
        self.enabled = False

    def start(self):
        self.enabled = True
        logger.info('[FlyingDamage] existing-marker renderer started')

    def stop(self):
        self.enabled = False
        _cancelRestores()
        logger.info('[FlyingDamage] existing-marker renderer stopped')

    def showOnVehicle(self, vehicleID, damage, colorRGB, fontSize, alpha, lifeTime):
        if not self.enabled:
            return False
        if _markerPlugin[0] is None:
            logger.info('[FlyingDamage] marker plugin not ready; cannot show d=%s vid=%s', int(damage), vehicleID)
            return False

        markerID = _getExistingMarkerID(vehicleID)
        if markerID is None:
            logger.info('[FlyingDamage] existing marker not found vid=%s d=%s', vehicleID, int(damage))
            return False

        txt = str(int(damage))
        try:
            labelOK = _setTextLabelEnabled(markerID, True)
            textOK = _setCustomDistanceText(markerID, txt)
            _invokeMarker(markerID, 'update')

            if _pushLog[0] < 80:
                _pushLog[0] += 1
                logger.info('[FlyingDamage] EXISTING_MARKER show d=%s vid=%s markerID=%s text=%s labelOK=%s textOK=%s',
                            int(damage), vehicleID, markerID, txt, labelOK, textOK)

            self._scheduleRestore(markerID, max(0.5, float(lifeTime)))
            return True
        except Exception:
            logger.error('[FlyingDamage] existing marker show failed vid=%s markerID=%s',
                         vehicleID, markerID, exc_info=True)
            return False

    def showDebug(self):
        if _markerPlugin[0] is None:
            logger.info('[FlyingDamage] existing-marker debug: plugin not ready')
            return False
        markerID = _getAnyExistingMarkerID()
        if markerID is None:
            logger.info('[FlyingDamage] existing-marker debug: no existing markers yet')
            return False
        try:
            labelOK = _setTextLabelEnabled(markerID, True)
            textOK = _setCustomDistanceText(markerID, '9999')
            _invokeMarker(markerID, 'update')
            logger.info('[FlyingDamage] EXISTING_MARKER debug markerID=%s text=9999 labelOK=%s textOK=%s',
                        markerID, labelOK, textOK)
            self._scheduleRestore(markerID, 5.0)
            return True
        except Exception:
            logger.error('[FlyingDamage] existing-marker debug failed', exc_info=True)
            return False

    def _scheduleRestore(self, markerID, lifeTime):
        try:
            old = _restoreCallbacks.pop(markerID, None)
            if old is not None:
                try:
                    BigWorld.cancelCallback(old)
                except Exception:
                    pass
            _restoreCallbacks[markerID] = BigWorld.callback(lifeTime, lambda: self._restore(markerID))
        except Exception:
            logger.error('[FlyingDamage] schedule restore failed markerID=%s', markerID, exc_info=True)

    def _restore(self, markerID):
        _restoreCallbacks.pop(markerID, None)
        if _markerPlugin[0] is None:
            return
        try:
            _setCustomDistanceText(markerID, '')
            _setTextLabelEnabled(markerID, False)
            _invokeMarker(markerID, 'update')
            logger.info('[FlyingDamage] EXISTING_MARKER restore markerID=%s', markerID)
        except Exception:
            logger.error('[FlyingDamage] existing marker restore failed markerID=%s', markerID, exc_info=True)


class Controller(object):

    def __init__(self):
        self._enabled = True
        self._battleMode = False
        self._renderer = _ExistingMarkerRenderer()

    def init(self):
        logger.info('[FlyingDamage] controller.init begin (existing vehicle markers via plugin)')
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
        logger.info('[FlyingDamage] avatar ready -> existing-marker renderer active')
        self._renderer.start()
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            pass
        BigWorld.callback(2.0, self._debugTestDamage)
        BigWorld.callback(5.0, self._debugTestDamage)
        BigWorld.callback(8.0, self._debugTestDamage)
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def _debugTestDamage(self):
        if not self._battleMode or _testLog[0]:
            return
        if self._renderer.showDebug():
            _testLog[0] = True

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
        if _pushLog[0] < 10:
            _pushLog[0] += 1
            logger.info('[FlyingDamage] screen damage ignored by existing-marker renderer d=%s', int(damage))

    def showDamageWorld(self, wx, wy, wz, fallbackX, fallbackY, damage, colorRGB,
                        fontSize, alpha, riseMeters=1.35, lifeTime=1.6, vehicleID=None):
        if not self._battleMode:
            return
        if vehicleID is None:
            if _pushLog[0] < 10:
                _pushLog[0] += 1
                logger.info('[FlyingDamage] missing vehicleID for existing-marker damage d=%s', int(damage))
            return
        self._renderer.showOnVehicle(vehicleID, damage, colorRGB, fontSize, alpha, lifeTime)

    def showDamage(self, x, y, damage, colorRGB, fontSize, alpha):
        self.showDamageAt(x, y, damage, colorRGB, fontSize, alpha)


g_controller = Controller()

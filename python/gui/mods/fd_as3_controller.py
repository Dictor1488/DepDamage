# -*- coding: utf-8 -*-
import logging

from PlayerEvents import g_playerEvents

logger = logging.getLogger(__name__)


class Controller(object):
    """
    Controller now only installs the marker hooks/settings.

    Damage rendering is intentionally returned to the native VehicleMarker path:
    VehicleMarkerPlugin._updateHealthMarker -> original VehicleMarker.addDamageLabel().
    No FlyingDamageApp overlay SWF is spawned for damage numbers.
    """

    def __init__(self):
        self._battleMode = False

    def init(self):
        logger.info('[FD_AS3] controller init native VehicleMarker damage path')
        try:
            from flyingdamage.settings.config import g_config
            g_config.registerSettings()
        except Exception:
            logger.error('[FD_AS3] settings failed', exc_info=True)
        try:
            from flyingdamage.hooks import installHooks
            installHooks()
        except Exception:
            logger.error('[FD_AS3] hooks failed', exc_info=True)
        try:
            from flyingdamage.suppress import installSuppression, setFeed
            setFeed(None)
            installSuppression()
        except Exception:
            logger.error('[FD_AS3] marker hook install failed', exc_info=True)
        g_playerEvents.onAvatarReady += self._onAvatarReady
        g_playerEvents.onAvatarBecomeNonPlayer += self._onBattleLeave

    def fini(self):
        logger.info('[FD_AS3] controller fini')
        try:
            g_playerEvents.onAvatarReady -= self._onAvatarReady
            g_playerEvents.onAvatarBecomeNonPlayer -= self._onBattleLeave
        except Exception:
            pass
        self._battleMode = False
        try:
            from flyingdamage.utils import restore_overrides
            restore_overrides()
        except Exception:
            pass

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        logger.info('[FD_AS3] avatar ready native VehicleMarker damage path')

    def onMarkerPluginStart(self):
        # Kept for compatibility with suppress._pluginStartHook.
        if not self._battleMode:
            return
        try:
            from flyingdamage.hooks import setView
            setView(self)
        except Exception:
            pass

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FD_AS3] battle leave')
        self._battleMode = False
        try:
            from flyingdamage.hooks import resetState
            resetState()
        except Exception:
            pass
        try:
            from flyingdamage.suppress import resetState as suppressReset
            suppressReset()
        except Exception:
            pass


g_controller = Controller()

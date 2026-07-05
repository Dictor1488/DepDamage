# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Registers a Scaleform battle View bound to FlyingDamageApp.swf, loads it on
# battle start, and feeds damage numbers to it. The SWF (an AbstractView) is
# Scaleform-compatible, so its AS3 actually runs.

import logging

import BigWorld
from PlayerEvents import g_playerEvents

logger = logging.getLogger(__name__)

_LINKAGE_BATTLE = 'FlyingDamageApp'
_SWF_BATTLE = 'FlyingDamageApp.swf'
_INJECT_MAX_ATTEMPTS = 40
_INJECT_RETRY_DELAY = 0.5


# ---------------------------------------------------------------------------
# Scaleform View bound to our SWF
# ---------------------------------------------------------------------------

def _makeViewClass():
    from gui.Scaleform.framework.entities.View import View

    class FlyingDamageBattleView(View):
        _g_controller = None

        def _populate(self):
            super(FlyingDamageBattleView, self)._populate()
            logger.info('[FlyingDamage] view _populate')
            if FlyingDamageBattleView._g_controller:
                FlyingDamageBattleView._g_controller._onViewReady(self)

        def _dispose(self):
            if FlyingDamageBattleView._g_controller:
                FlyingDamageBattleView._g_controller._onViewDisposed(self)
            super(FlyingDamageBattleView, self)._dispose()

        def py_log(self, msg):
            logger.info('[FlyingDamage] %s', msg)

    return FlyingDamageBattleView


class Controller(object):

    def __init__(self):
        self._enabled = True
        self._battleMode = False
        self._view = None
        self._viewClass = None
        self._registered = False
        self._bridgeLog = 0

    # -- lifecycle ------------------------------------------------------

    def init(self):
        logger.info('[FlyingDamage] controller.init begin')

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

        # Install standard-damage suppression early (before marker plugins are
        # created), so the class method is already wrapped.
        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamage] early suppression failed', exc_info=True)

        self._registerFlash()

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
        self._destroyView()
        self._unregisterFlash()
        try:
            from .utils import restore_overrides
            restore_overrides()
        except Exception:
            pass

    # -- flash registration --------------------------------------------

    def _registerFlash(self):
        if self._registered:
            return
        try:
            from gui.Scaleform.framework import (
                g_entitiesFactories, ScopeTemplates, ViewSettings)
            from frameworks.wulf import WindowLayer

            self._viewClass = _makeViewClass()
            self._viewClass._g_controller = self

            g_entitiesFactories.addSettings(ViewSettings(
                _LINKAGE_BATTLE, self._viewClass, _SWF_BATTLE,
                WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
            self._registered = True
            logger.info('[FlyingDamage] flash view registered')
        except Exception:
            logger.error('[FlyingDamage] registerFlash failed', exc_info=True)

    def _unregisterFlash(self):
        if not self._registered:
            return
        try:
            from gui.Scaleform.framework import g_entitiesFactories
            g_entitiesFactories.removeSettings(_LINKAGE_BATTLE)
        except Exception:
            pass
        self._registered = False

    # -- battle lifecycle ----------------------------------------------

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        logger.info('[FlyingDamage] avatar ready -> injecting battle view')
        self._injectBattleFlash()
        # Suppress standard damage after battle UI (and its SWF) has loaded.
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def _installSuppressionSafe(self):
        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamage] installSuppression failed', exc_info=True)

    def _injectBattleFlash(self, attempt=0):
        if not self._battleMode:
            return
        try:
            from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
            from gui.shared.personality import ServicesLocator
            app = ServicesLocator.appLoader.getDefBattleApp()
            if app and app.initialized:
                app.loadView(SFViewLoadParams(_LINKAGE_BATTLE))
                logger.info('[FlyingDamage] loadView requested')
                return
        except Exception:
            logger.error('[FlyingDamage] inject failed (attempt=%d)', attempt,
                         exc_info=True)
        if attempt < _INJECT_MAX_ATTEMPTS:
            BigWorld.callback(_INJECT_RETRY_DELAY,
                              lambda: self._injectBattleFlash(attempt + 1))

    def _onViewReady(self, view):
        self._view = view
        logger.info('[FlyingDamage] view ready, wiring flashObject')
        try:
            view.flashObject.py_log = view.py_log
            view.flashObject.py_getScreenPos = self._py_getScreenPos
        except Exception:
            logger.error('[FlyingDamage] wiring callbacks failed', exc_info=True)
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            logger.error('[FlyingDamage] setView failed', exc_info=True)

    def _py_getScreenPos(self, vehicleID):
        """Called by the SWF each frame to keep the number stuck to the tank."""
        try:
            from .hooks import projectVehicleScreen
            return projectVehicleScreen(int(vehicleID))
        except Exception:
            return None

    def _onViewDisposed(self, view):
        if self._view is view:
            self._view = None
        try:
            from .hooks import setView
            setView(None)
        except Exception:
            pass

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FlyingDamage] battle leave')
        self._battleMode = False
        self._destroyView()
        try:
            from .hooks import resetState
            resetState()
        except Exception:
            pass
        try:
            from .suppress import resetState as suppressReset
            suppressReset()
        except Exception:
            pass

    def _destroyView(self):
        self._view = None

    # -- called by hooks to draw a number -------------------------------

    def showDamage(self, vehicleID, damage, colorRGB, fontSize, alpha):
        v = self._view
        if v is None:
            logger.info('[FlyingDamage] showDamage but view is None (dmg=%s)', damage)
            return
        try:
            fo = v.flashObject
            if fo is not None:
                if self._bridgeLog < 10:
                    self._bridgeLog += 1
                    logger.info('[FlyingDamage] -> as_showDamage vid=%s dmg=%s',
                                vehicleID, damage)
                fo.as_showDamage(
                    float(vehicleID), int(damage),
                    int(colorRGB), int(fontSize), float(alpha))
            else:
                logger.info('[FlyingDamage] showDamage but flashObject None')
        except Exception:
            logger.error('[FlyingDamage] as_showDamage bridge failed', exc_info=True)


g_controller = Controller()

# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Gameface renderer for FlyingDamage. No AS3/SWF bridge is used.
# Python catches damage, projects the vehicle to screen pixels, then pushes a
# JSON payload into a fullscreen WULF/Gameface overlay. JS draws the numbers.

import json
import logging

import BigWorld
import GUI
from PlayerEvents import g_playerEvents

logger = logging.getLogger(__name__)

RES_MAP_ITEM_ID = 'mods/flyingdamage/FlyingDamageBattle/layoutID'

_OPENWG_OK = False
_OPENWG_ERR = None
_IMPORT_STAGE = 'start'
try:
    _IMPORT_STAGE = 'frameworks.wulf'
    from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags, WindowLayer, WindowSettings

    _IMPORT_STAGE = 'gui.impl.pub'
    from gui.impl.pub import ViewImpl, WindowImpl

    _IMPORT_STAGE = 'openwg_gameface.ModDynAccessor'
    from openwg_gameface import ModDynAccessor

    _OPENWG_OK = True
except Exception as _e:
    ViewModel = object
    ViewSettings = None
    ViewFlags = None
    WindowFlags = None
    WindowLayer = None
    WindowSettings = None
    ViewImpl = object
    WindowImpl = object
    ModDynAccessor = None
    _OPENWG_OK = False
    _OPENWG_ERR = '%s: %s' % (_IMPORT_STAGE, _e)


if _OPENWG_OK:
    class FlyingDamageModel(ViewModel):
        """One string payload, same practical pattern as CustomHPBarGF."""

        def __init__(self, properties=1, commands=0):
            super(FlyingDamageModel, self).__init__(properties=properties, commands=commands)

        def _initialize(self):
            super(FlyingDamageModel, self)._initialize()
            self._addStringProperty('payload', '{}')

        def getPayload(self):
            return self._getString(0)

        def setPayload(self, value):
            self._setString(0, value)


    class FlyingDamageView(ViewImpl):
        viewLayoutID = ModDynAccessor(RES_MAP_ITEM_ID)

        def __init__(self):
            layoutID = FlyingDamageView.viewLayoutID()
            logger.info('[FlyingDamageGF] resolved layoutID=%s for %s', layoutID, RES_MAP_ITEM_ID)
            settings = ViewSettings(layoutID, flags=ViewFlags.VIEW, model=FlyingDamageModel())
            super(FlyingDamageView, self).__init__(settings)
            self._lastRaw = None

        @property
        def viewModel(self):
            return self.getViewModel()

        def pushDamage(self, payload):
            raw = json.dumps(payload, separators=(',', ':'))
            if raw == self._lastRaw:
                return
            self._lastRaw = raw
            with self.viewModel.transaction() as model:
                model.setPayload(raw)


    class FlyingDamageWindow(WindowImpl):

        def __init__(self):
            content = FlyingDamageView()
            flags = WindowFlags.WINDOW
            try:
                flags = flags | WindowFlags.WINDOW_FULLSCREEN
            except Exception:
                pass
            try:
                settings = WindowSettings(flags, content=content, layer=WindowLayer.TOP_WINDOW)
                super(FlyingDamageWindow, self).__init__(settings)
                logger.info('[FlyingDamageGF] fullscreen window settings TOP_WINDOW')
            except Exception:
                try:
                    settings = WindowSettings(flags, content=content, layer=WindowLayer.VIEW)
                    super(FlyingDamageWindow, self).__init__(settings)
                    logger.info('[FlyingDamageGF] fullscreen window settings VIEW')
                except Exception:
                    super(FlyingDamageWindow, self).__init__(wndFlags=flags, content=content)
                    logger.info('[FlyingDamageGF] fallback WindowImpl wndFlags=%s', flags)
else:
    FlyingDamageWindow = None


class Controller(object):

    def __init__(self):
        self._battleMode = False
        self._window = None
        self._view = None
        self._seq = 0
        self._pushLog = 0
        self._loadTried = False

    def init(self):
        logger.info('[FlyingDamageGF] controller.init begin')
        if not _OPENWG_OK:
            logger.error('[FlyingDamageGF] OpenWG/Gameface imports failed: %s', _OPENWG_ERR)
        else:
            logger.info('[FlyingDamageGF] OpenWG/Gameface imports OK')

        try:
            from .settings.config import g_config
            g_config.registerSettings()
        except Exception:
            logger.error('[FlyingDamageGF] settings failed', exc_info=True)

        try:
            from .hooks import installHooks
            installHooks()
        except Exception:
            logger.error('[FlyingDamageGF] installHooks failed', exc_info=True)

        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamageGF] suppression failed', exc_info=True)

        g_playerEvents.onAvatarReady += self._onAvatarReady
        g_playerEvents.onAvatarBecomeNonPlayer += self._onBattleLeave
        logger.info('[FlyingDamageGF] controller.init done')

    def fini(self):
        logger.info('[FlyingDamageGF] controller.fini')
        try:
            g_playerEvents.onAvatarReady -= self._onAvatarReady
            g_playerEvents.onAvatarBecomeNonPlayer -= self._onBattleLeave
        except Exception:
            pass
        self._destroyWindow()
        try:
            from .utils import restore_overrides
            restore_overrides()
        except Exception:
            pass

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        logger.info('[FlyingDamageGF] avatar ready')
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            pass
        BigWorld.callback(1.0, self._loadWindow)
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def onMarkerPluginStart(self):
        logger.info('[FlyingDamageGF] marker plugin start')
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            pass
        self._loadWindow()

    def _installSuppressionSafe(self):
        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamageGF] installSuppression failed', exc_info=True)

    def _loadWindow(self):
        if self._window is not None:
            return True
        if not _OPENWG_OK or FlyingDamageWindow is None:
            if not self._loadTried:
                self._loadTried = True
                logger.error('[FlyingDamageGF] cannot load window: OpenWG/Gameface unavailable: %s', _OPENWG_ERR)
            return False
        try:
            self._window = FlyingDamageWindow()
            self._window.load()
            self._view = getattr(self._window, 'content', None)
            if self._view is None:
                self._view = getattr(self._window, '_WindowImpl__content', None)
            if self._view is None:
                try:
                    self._view = self._window.content
                except Exception:
                    pass
            logger.info('[FlyingDamageGF] Gameface window loaded view=%s', self._view is not None)
            return True
        except Exception:
            logger.error('[FlyingDamageGF] Gameface window load failed', exc_info=True)
            self._window = None
            self._view = None
            return False

    def _destroyWindow(self):
        try:
            if self._window is not None:
                self._window.destroy()
        except Exception:
            pass
        self._window = None
        self._view = None
        try:
            from .hooks import setView
            setView(None)
        except Exception:
            pass

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FlyingDamageGF] battle leave')
        self._battleMode = False
        self._destroyWindow()
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

    def showDamage(self, vehicleID, damage, colorRGB, fontSize, alpha):
        if damage <= 0:
            return
        if self._window is None or self._view is None:
            self._loadWindow()
        if self._view is None:
            if self._pushLog < 20:
                self._pushLog += 1
                logger.info('[FlyingDamageGF] skip damage: view not ready vid=%s dmg=%s', vehicleID, damage)
            return

        try:
            from .hooks import projectVehicleScreen
            pos = projectVehicleScreen(int(vehicleID))
        except Exception:
            pos = None

        if not pos or not pos.get('ok'):
            if self._pushLog < 80:
                self._pushLog += 1
                logger.info('[FlyingDamageGF] skip damage: no screen pos vid=%s dmg=%s pos=%s', vehicleID, damage, pos)
            return

        try:
            sw, sh = GUI.screenResolution()[:2]
        except Exception:
            sw, sh = 1920, 1080

        self._seq += 1
        ev = {
            'id': self._seq,
            'vid': int(vehicleID),
            'dmg': int(damage),
            'x': float(pos.get('x', 0.0)),
            'y': float(pos.get('y', 0.0)),
            'sw': int(sw),
            'sh': int(sh),
            'color': int(colorRGB) & 0xFFFFFF,
            'size': int(fontSize),
            'alpha': float(alpha),
            'life': 1.6
        }
        payload = {'seq': self._seq, 'events': [ev]}
        try:
            self._view.pushDamage(payload)
            if self._pushLog < 120:
                self._pushLog += 1
                logger.info('[FlyingDamageGF] push damage id=%s vid=%s dmg=%s xy=(%.1f,%.1f) screen=%sx%s',
                            self._seq, int(vehicleID), int(damage), ev['x'], ev['y'], sw, sh)
        except Exception:
            logger.error('[FlyingDamageGF] pushDamage failed', exc_info=True)


g_controller = Controller()

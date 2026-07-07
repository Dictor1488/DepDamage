# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Gameface renderer for FlyingDamage. Single battle-wide WULF window.

import json
import logging
import time

import BigWorld
import GUI
from PlayerEvents import g_playerEvents

logger = logging.getLogger(__name__)

RES_MAP_ITEM_ID = 'mods/flyingdamage/FlyingDamageBattle/layoutID'
VIEW_W = 2560
VIEW_H = 1369
DAMAGE_LIFE = 1.8
UPDATE_INTERVAL = 0.08
MAX_ACTIVE = 24

_OPENWG_OK = False
_OPENWG_ERR = None
_IMPORT_STAGE = 'start'
try:
    _IMPORT_STAGE = 'frameworks.wulf'
    from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags, WindowLayer, WindowStatus

    _IMPORT_STAGE = 'gui.impl.pub'
    from gui.impl.pub import ViewImpl, WindowImpl

    _IMPORT_STAGE = 'openwg_gameface'
    from openwg_gameface import ModDynAccessor, manager as gamefaceResMap, on_ready as gamefaceOnReady

    _IMPORT_STAGE = 'IGuiLoader'
    from helpers import dependency
    from skeletons.gui.impl import IGuiLoader

    _OPENWG_OK = True
except Exception as _e:
    ViewModel = object
    ViewSettings = None
    ViewFlags = None
    WindowFlags = None
    WindowLayer = None
    WindowStatus = None
    ViewImpl = object
    WindowImpl = object
    ModDynAccessor = None
    gamefaceResMap = None
    gamefaceOnReady = None
    dependency = None
    IGuiLoader = None
    _OPENWG_OK = False
    _OPENWG_ERR = '%s: %s' % (_IMPORT_STAGE, _e)


if _OPENWG_OK:
    _LAYOUT = ModDynAccessor(RES_MAP_ITEM_ID)

    class FlyingDamageModel(ViewModel):
        def __init__(self):
            super(FlyingDamageModel, self).__init__(properties=1, commands=1)

        def _initialize(self):
            super(FlyingDamageModel, self)._initialize()
            self._addStringProperty('payload', '{}')
            self.onReady = self._addCommand('onReady')

        def setPayload(self, value):
            self._setString(0, value)


    class FlyingDamageView(ViewImpl):
        def __init__(self, controller):
            self._controller = controller
            self._model = FlyingDamageModel()
            layoutID = _LAYOUT()
            logger.info('[FlyingDamageGF] single layoutID=%s for %s', layoutID, RES_MAP_ITEM_ID)
            settings = ViewSettings(layoutID=layoutID, flags=ViewFlags.VIEW, model=self._model)
            super(FlyingDamageView, self).__init__(settings)

        def _getEvents(self):
            return ((self.getViewModel().onReady, self._controller._onViewReady),)

        def _finalize(self):
            self._controller._onViewFinalized()
            super(FlyingDamageView, self)._finalize()

        def pushPayload(self, payload):
            try:
                self._model.setPayload(payload)
            except Exception:
                logger.error('[FlyingDamageGF] setPayload failed', exc_info=True)


    class FlyingDamageWindow(WindowImpl):
        def __init__(self, content, parent):
            super(FlyingDamageWindow, self).__init__(WindowFlags.WINDOW,
                                                     content=content,
                                                     layer=WindowLayer.OVERLAY,
                                                     name='FlyingDamageSingleWindow',
                                                     parent=parent)
else:
    FlyingDamageView = object
    FlyingDamageWindow = object


class Controller(object):

    def __init__(self):
        self._battleMode = False
        self._seq = 0
        self._pushLog = 0
        self._window = None
        self._view = None
        self._ready = False
        self._loadToken = 0
        self._updateCb = None
        self._active = []

    def init(self):
        logger.info('[FlyingDamageGF] controller.init begin')
        if not _OPENWG_OK:
            logger.error('[FlyingDamageGF] OpenWG/Gameface imports failed: %s', _OPENWG_ERR)
        else:
            logger.info('[FlyingDamageGF] OpenWG/Gameface imports OK single-window mode')

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
        self._battleMode = False
        self._stopUpdater()
        self._destroyWindow()
        try:
            from .utils import restore_overrides
            restore_overrides()
        except Exception:
            pass

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        self._active = []
        logger.info('[FlyingDamageGF] avatar ready single-window')
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            pass
        self._loadWindow()
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def onMarkerPluginStart(self):
        logger.info('[FlyingDamageGF] marker plugin start')
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            pass
        if self._battleMode and self._window is None:
            self._loadWindow()

    def _installSuppressionSafe(self):
        if not self._battleMode:
            return
        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamageGF] installSuppression failed', exc_info=True)

    def _loadWindow(self):
        if not _OPENWG_OK or not self._battleMode or self._window is not None:
            return
        self._loadToken += 1
        token = self._loadToken
        if gamefaceResMap is not None and not gamefaceResMap.isResMapValidated:
            gamefaceOnReady(lambda: self._loadWindowImpl(token))
        else:
            self._loadWindowImpl(token)

    def _loadWindowImpl(self, token, retry=0):
        if token != self._loadToken or not self._battleMode or self._window is not None:
            return
        try:
            parent = dependency.instance(IGuiLoader).windowsManager.getMainWindow()
        except Exception:
            parent = None
        if parent is None or getattr(parent, 'proxy', None) is None or parent.windowStatus != WindowStatus.LOADED:
            if retry < 80 and self._battleMode:
                BigWorld.callback(0.1, lambda: self._loadWindowImpl(token, retry + 1))
            return
        try:
            self._view = FlyingDamageView(self)
            self._window = FlyingDamageWindow(self._view, parent)
            self._window.load()
            try:
                self._window.move(0, 0)
            except Exception:
                pass
            logger.info('[FlyingDamageGF] single window load requested %sx%s', VIEW_W, VIEW_H)
        except Exception:
            logger.error('[FlyingDamageGF] single window load failed', exc_info=True)
            self._destroyWindow()

    def _onViewReady(self, *args):
        if not self._battleMode:
            self._destroyWindow()
            return
        self._ready = True
        try:
            if self._window is not None:
                self._window.move(0, 0)
        except Exception:
            pass
        logger.info('[FlyingDamageGF] single view ready')
        self._pushPayload(force=True)
        self._scheduleUpdater()

    def _onViewFinalized(self):
        self._ready = False
        self._view = None
        self._window = None
        self._stopUpdater()

    def _destroyWindow(self):
        self._loadToken += 1
        self._ready = False
        self._active = []
        self._stopUpdater()
        win = self._window
        self._window = None
        self._view = None
        if win is not None:
            try:
                win.destroy()
            except Exception:
                pass
        try:
            from .hooks import setView
            setView(None)
        except Exception:
            pass

    def _stopUpdater(self):
        try:
            if self._updateCb is not None:
                BigWorld.cancelCallback(self._updateCb)
        except Exception:
            pass
        self._updateCb = None

    def _scheduleUpdater(self):
        if not self._battleMode or not self._ready:
            return
        self._updateCb = BigWorld.callback(UPDATE_INTERVAL, self._update)

    def _update(self):
        self._updateCb = None
        if not self._battleMode or not self._ready:
            return
        self._pushPayload(force=False)
        self._scheduleUpdater()

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FlyingDamageGF] battle leave single-window')
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
        if damage <= 0 or not self._battleMode:
            return
        if not _OPENWG_OK:
            return
        if self._window is None:
            self._loadWindow()

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

        now = time.time()
        self._seq += 1
        item = {
            'id': self._seq,
            'vid': int(vehicleID),
            'dmg': int(damage),
            'color': int(colorRGB) & 0xFFFFFF,
            'alpha': float(alpha),
            'start': now,
            'life': DAMAGE_LIFE,
            'x': float(pos.get('x', 0.0)),
            'y': float(pos.get('y', 0.0))
        }
        self._active.append(item)
        if len(self._active) > MAX_ACTIVE:
            self._active = self._active[-MAX_ACTIVE:]
        if self._pushLog < 120:
            self._pushLog += 1
            logger.info('[FlyingDamageGF] single add id=%s vid=%s dmg=%s xy=(%.1f,%.1f) active=%s',
                        self._seq, int(vehicleID), int(damage), item['x'], item['y'], len(self._active))
        self._pushPayload(force=True)

    def _pushPayload(self, force=False):
        if not self._battleMode or not self._ready or self._view is None:
            return
        now = time.time()
        events = []
        alive = []
        try:
            from .hooks import projectVehicleScreen
        except Exception:
            projectVehicleScreen = None
        for item in self._active:
            age = now - item.get('start', now)
            life = item.get('life', DAMAGE_LIFE)
            if age > life:
                continue
            if projectVehicleScreen is not None:
                try:
                    pos = projectVehicleScreen(int(item['vid']), quiet=True)
                except Exception:
                    pos = None
                if pos and pos.get('ok'):
                    item['x'] = float(pos.get('x', item['x']))
                    item['y'] = float(pos.get('y', item['y']))
            ev = {
                'id': int(item['id']),
                'vid': int(item['vid']),
                'dmg': int(item['dmg']),
                'x': float(item['x']),
                'y': float(item['y']),
                'color': int(item['color']) & 0xFFFFFF,
                'alpha': float(item.get('alpha', 1.0)),
                'age': float(age),
                'life': float(life)
            }
            events.append(ev)
            alive.append(item)
        self._active = alive
        payload = {
            'seq': self._seq,
            'events': events,
            'sw': int(GUI.screenResolution()[0]),
            'sh': int(GUI.screenResolution()[1]),
            'vw': VIEW_W,
            'vh': VIEW_H
        }
        try:
            self._view.pushPayload(json.dumps(payload, separators=(',', ':')))
        except Exception:
            logger.error('[FlyingDamageGF] push payload failed', exc_info=True)


g_controller = Controller()

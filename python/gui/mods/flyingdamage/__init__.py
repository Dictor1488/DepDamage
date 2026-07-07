# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Gameface renderer for FlyingDamage. No AS3/SWF bridge is used.
# Small WULF WindowLayer.OVERLAY popup windows are moved to projected damage coordinates.

import json
import logging

import BigWorld
import GUI
from PlayerEvents import g_playerEvents

logger = logging.getLogger(__name__)

RES_MAP_ITEM_ID = 'mods/flyingdamage/FlyingDamageBattle/layoutID'
POPUP_W = 220
POPUP_H = 120
POPUP_LIFE = 3.2
POPUP_DESTROY_DELAY = 4.8
POPUP_TRACK_INTERVAL = 0.033

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

    class _DamageModel(ViewModel):
        def __init__(self, payload):
            self._payload = payload
            super(_DamageModel, self).__init__(properties=1, commands=1)

        def _initialize(self):
            super(_DamageModel, self)._initialize()
            self._addStringProperty('payload', self._payload)
            self.onReady = self._addCommand('onReady')

        def setPayload(self, value):
            self._setString(0, value)


    class _DamageView(ViewImpl):
        def __init__(self, popup):
            self._popup = popup
            model = _DamageModel(popup.payload())
            popup._setModel(model)
            layoutID = _LAYOUT()
            logger.info('[FlyingDamageGF] popup layoutID=%s for %s', layoutID, RES_MAP_ITEM_ID)
            settings = ViewSettings(layoutID=layoutID, flags=ViewFlags.VIEW, model=model)
            super(_DamageView, self).__init__(settings)

        def _getEvents(self):
            return ((self.getViewModel().onReady, self._popup.onReady),)

        def _finalize(self):
            self._popup._setModel(None)
            super(_DamageView, self)._finalize()
            self._popup.onFinalized()


    class _DamageWindow(WindowImpl):
        def __init__(self, content, parent, name):
            super(_DamageWindow, self).__init__(WindowFlags.WINDOW,
                                                content=content,
                                                layer=WindowLayer.OVERLAY,
                                                name=name,
                                                parent=parent)


    class _DamagePopup(object):
        def __init__(self, owner, vehicleID, payload, x, y, life):
            self._owner = owner
            self._vehicleID = int(vehicleID)
            self._payload = payload
            self._x = int(round(x))
            self._y = int(round(y))
            self._life = float(life)
            self._window = None
            self._model = None
            self._ready = False
            self._token = 0
            self._destroyed = False
            self._cb = None
            self._trackCb = None
            self._trackLog = 0

        def payload(self):
            return json.dumps(self._payload, separators=(',', ':'))

        def _setModel(self, model):
            self._model = model

        def load(self):
            if self._destroyed:
                return
            self._token += 1
            token = self._token
            if gamefaceResMap is not None and not gamefaceResMap.isResMapValidated:
                gamefaceOnReady(lambda: self._load(token))
            else:
                self._load(token)

        def _load(self, token, retry=0):
            if token != self._token or self._destroyed:
                return
            try:
                parent = dependency.instance(IGuiLoader).windowsManager.getMainWindow()
            except Exception:
                parent = None
            if parent is None or getattr(parent, 'proxy', None) is None or parent.windowStatus != WindowStatus.LOADED:
                if retry < 100:
                    BigWorld.callback(0.1, lambda: self._load(token, retry + 1))
                return
            try:
                self._window = _DamageWindow(_DamageView(self), parent, 'FlyingDamagePopup')
                self._window.load()
                logger.info('[FlyingDamageGF] popup window load requested vid=%s at x=%s y=%s life=%.2f', self._vehicleID, self._x, self._y, self._life)
            except Exception:
                logger.error('[FlyingDamageGF] popup window load failed', exc_info=True)
                self.destroy()

        def onReady(self, *args):
            if self._destroyed:
                return
            self._ready = True
            self._updateMarkerPosition()
            self.move()
            self._scheduleTrack()
            self._cb = BigWorld.callback(POPUP_DESTROY_DELAY, self.destroy)
            logger.info('[FlyingDamageGF] popup ready tracked vid=%s x=%s y=%s keep=%.2f', self._vehicleID, self._x, self._y, POPUP_DESTROY_DELAY)

        def _scheduleTrack(self):
            if self._destroyed or not self._ready:
                return
            self._trackCb = BigWorld.callback(POPUP_TRACK_INTERVAL, self._track)

        def _track(self):
            self._trackCb = None
            if self._destroyed or not self._ready:
                return
            self._updateMarkerPosition()
            self.move()
            self._scheduleTrack()

        def _updateMarkerPosition(self):
            try:
                from .hooks import projectVehicleScreen
                pos = projectVehicleScreen(self._vehicleID)
            except Exception:
                pos = None
            if pos and pos.get('ok'):
                self._x = int(round(float(pos.get('x', self._x))))
                self._y = int(round(float(pos.get('y', self._y))))
                if self._trackLog < 3:
                    self._trackLog += 1
                    logger.info('[FlyingDamageGF] popup track vid=%s x=%s y=%s', self._vehicleID, self._x, self._y)

        def move(self):
            if self._window is None or not self._ready:
                return
            try:
                sw, sh = GUI.screenResolution()[:2]
            except Exception:
                sw, sh = 1920, 1080
            left = max(0, min(int(self._x - POPUP_W * 0.5), int(sw - POPUP_W)))
            top = max(0, min(int(self._y - POPUP_H * 0.65), int(sh - POPUP_H)))
            try:
                self._window.move(left, top)
            except Exception:
                pass

        def onFinalized(self):
            self._window = None
            self._model = None
            self._ready = False
            self._owner._forgetPopup(self)

        def destroy(self):
            self._destroyed = True
            self._token += 1
            try:
                if self._cb is not None:
                    BigWorld.cancelCallback(self._cb)
            except Exception:
                pass
            try:
                if self._trackCb is not None:
                    BigWorld.cancelCallback(self._trackCb)
            except Exception:
                pass
            self._cb = None
            self._trackCb = None
            if self._window is not None:
                try:
                    self._window.destroy()
                except Exception:
                    pass
            self._window = None
            self._model = None
            self._ready = False
            self._owner._forgetPopup(self)
else:
    _DamagePopup = None


class Controller(object):

    def __init__(self):
        self._battleMode = False
        self._seq = 0
        self._pushLog = 0
        self._popups = []

    def init(self):
        logger.info('[FlyingDamageGF] controller.init begin')
        if not _OPENWG_OK:
            logger.error('[FlyingDamageGF] OpenWG/Gameface imports failed: %s', _OPENWG_ERR)
        else:
            logger.info('[FlyingDamageGF] OpenWG/Gameface imports OK popup-window mode')

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
        self._destroyPopups()
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
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def onMarkerPluginStart(self):
        logger.info('[FlyingDamageGF] marker plugin start')
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            pass

    def _installSuppressionSafe(self):
        try:
            from .suppress import installSuppression, setFeed
            from .hooks import showDamageForVehicle
            setFeed(showDamageForVehicle)
            installSuppression()
        except Exception:
            logger.error('[FlyingDamageGF] installSuppression failed', exc_info=True)

    def _destroyPopups(self):
        for popup in list(self._popups):
            try:
                popup.destroy()
            except Exception:
                pass
        self._popups = []
        try:
            from .hooks import setView
            setView(None)
        except Exception:
            pass

    def _forgetPopup(self, popup):
        try:
            self._popups.remove(popup)
        except ValueError:
            pass

    def _onBattleLeave(self, *a, **kw):
        logger.info('[FlyingDamageGF] battle leave')
        self._battleMode = False
        self._destroyPopups()
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
        if not _OPENWG_OK or _DamagePopup is None:
            if self._pushLog < 20:
                self._pushLog += 1
                logger.info('[FlyingDamageGF] skip damage: Gameface unavailable vid=%s dmg=%s', vehicleID, damage)
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
            'x': POPUP_W * 0.5,
            'y': POPUP_H * 0.55,
            'sw': POPUP_W,
            'sh': POPUP_H,
            'color': int(colorRGB) & 0xFFFFFF,
            'size': int(fontSize),
            'alpha': float(alpha),
            'life': POPUP_LIFE
        }
        payload = {'seq': self._seq, 'events': [ev], 'w': POPUP_W, 'h': POPUP_H}
        popup = _DamagePopup(self, int(vehicleID), payload, float(pos.get('x', 0.0)), float(pos.get('y', 0.0)), ev['life'])
        self._popups.append(popup)
        popup.load()

        if self._pushLog < 160:
            self._pushLog += 1
            logger.info('[FlyingDamageGF] popup damage id=%s vid=%s dmg=%s screenxy=(%.1f,%.1f) screen=%sx%s active=%s',
                        self._seq, int(vehicleID), int(damage), float(pos.get('x', 0.0)), float(pos.get('y', 0.0)), sw, sh, len(self._popups))


g_controller = Controller()

# -*- coding: utf-8 -*-
# flyingdamage/__init__.py  --  Python 2.7
# Native GUI renderer for FlyingDamage.
#
# The earlier ExternalFlashComponent path logged correctly but did not render in
# this WoT battle layer. This build draws floating damage directly with native
# BigWorld GUI.Window + GUI.Text components, so it does not depend on a separate
# SWF being visible.

import logging

import BigWorld
import GUI

from PlayerEvents import g_playerEvents

logger = logging.getLogger(__name__)

try:
    from gui import g_guiResetters
except Exception:
    g_guiResetters = None

_SWF_NAME = 'FlyingDamageApp.swf'  # kept only for package compatibility
_pushLog = [0]
_testLog = [False]


def _screen_size():
    try:
        sw, sh = GUI.screenResolution()[:2]
        sw = float(sw)
        sh = float(sh)
        if sw <= 0.0 or sh <= 0.0:
            return 1920.0, 1080.0
        return sw, sh
    except Exception:
        return 1920.0, 1080.0


def _color_fmt(colorRGB, alpha=1.0):
    try:
        rgb = int(colorRGB) & 0xFFFFFF
    except Exception:
        rgb = 0xFFFFFF
    try:
        a = int(max(0.0, min(1.0, float(alpha))) * 255.0)
    except Exception:
        a = 255
    return '\\c%06X%02X;' % (rgb, a)


class _NativeDamageNumber(object):

    def __init__(self, manager, x, y, damage, colorRGB, fontSize, alpha,
                 risePixels, lifeTime, world=None, riseMeters=1.35):
        self.manager = manager
        self.startX = float(x)
        self.startY = float(y)
        self.damage = int(damage)
        self.colorRGB = int(colorRGB) & 0xFFFFFF
        self.baseAlpha = max(0.0, min(1.0, float(alpha)))
        self.risePixels = float(risePixels)
        self.lifeTime = max(0.15, float(lifeTime))
        self.world = world
        self.riseMeters = float(riseMeters)
        self.started = BigWorld.time()
        self.window = None
        self.shadow = None
        self.label = None
        self._create(int(fontSize))

    def _fontName(self, fontSize):
        # WoT font names are fixed resources; native GUI.Text does not use point
        # size directly. Pick a larger stock font for bigger configured numbers.
        if fontSize >= 34:
            return 'default_large.font'
        return 'default_medium.font'

    def _create(self, fontSize):
        try:
            self.window = GUI.Window('')
            self.window.materialFX = 'BLEND'
            self.window.verticalAnchor = 'TOP'
            self.window.horizontalAnchor = 'LEFT'
            self.window.horizontalPositionMode = 'PIXEL'
            self.window.verticalPositionMode = 'PIXEL'
            self.window.heightMode = 'PIXEL'
            self.window.widthMode = 'PIXEL'
            self.window.width = 220
            self.window.height = 90
            self.window.visible = True

            GUI.addRoot(self.window)

            font = self._fontName(fontSize)
            self.shadow = GUI.Text('')
            self._installText(self.shadow, font)
            self.label = GUI.Text('')
            self._installText(self.label, font)
            self.setText(self.damage, self.baseAlpha)
            self.update()
        except Exception:
            logger.error('[FlyingDamage] native number create failed', exc_info=True)
            self.dispose()

    def _installText(self, item, font):
        item.font = font
        item.verticalAnchor = 'TOP'
        item.horizontalAnchor = 'CENTER'
        item.horizontalPositionMode = 'PIXEL'
        item.verticalPositionMode = 'PIXEL'
        item.position = (self.window.width / 2, 0, 1)
        item.colourFormatting = True
        item.visible = True
        self.window.addChild(item)

    def setText(self, damage, alpha):
        text = str(int(damage))
        try:
            self.shadow.text = '\\c000000%02X;%s' % (int(alpha * 255.0), text)
            self.label.text = _color_fmt(self.colorRGB, alpha) + text
            # Offset shadow slightly down/right by moving its child position.
            self.shadow.position = (self.window.width / 2 + 2, 2, 1)
            self.label.position = (self.window.width / 2, 0, 1)
        except Exception:
            pass

    def _projectWorld(self, progress):
        if self.world is None:
            return None
        try:
            from .hooks import projectWorldPoint
            wx, wy, wz = self.world
            pos = projectWorldPoint(wx, wy + self.riseMeters * progress, wz)
            if pos and pos.get('ok'):
                return float(pos.get('x', self.startX)), float(pos.get('y', self.startY))
        except Exception:
            pass
        return None

    def update(self):
        try:
            now = BigWorld.time()
            age = now - self.started
            if age >= self.lifeTime:
                return False
            progress = age / self.lifeTime

            worldPos = self._projectWorld(progress)
            if worldPos is not None:
                x, y = worldPos
            else:
                x = self.startX
                y = self.startY - self.risePixels * progress

            fadeStart = 0.55
            if progress <= fadeStart:
                alpha = self.baseAlpha
            else:
                alpha = self.baseAlpha * (1.0 - (progress - fadeStart) / (1.0 - fadeStart))
                if alpha < 0.0:
                    alpha = 0.0
            self.setText(self.damage, alpha)

            if self.window is not None:
                self.window.position = (x - self.window.width / 2, y - self.window.height / 2, 1)
                self.window.visible = True
            return True
        except Exception:
            logger.error('[FlyingDamage] native number update failed', exc_info=True)
            return False

    def dispose(self):
        try:
            if self.window is not None:
                GUI.delRoot(self.window)
        except Exception:
            pass
        self.window = None
        self.shadow = None
        self.label = None


class _NativeDamageRenderer(object):

    def __init__(self):
        self.items = []
        self._cb = None
        self.enabled = False

    def start(self):
        self.enabled = True
        self._schedule()
        logger.info('[FlyingDamage] native GUI renderer started')

    def stop(self):
        self.enabled = False
        if self._cb is not None:
            try:
                BigWorld.cancelCallback(self._cb)
            except Exception:
                pass
            self._cb = None
        for item in list(self.items):
            item.dispose()
        del self.items[:]
        logger.info('[FlyingDamage] native GUI renderer stopped')

    def _schedule(self):
        if not self.enabled or self._cb is not None:
            return
        self._cb = BigWorld.callback(0.016, self._tick)

    def _tick(self):
        self._cb = None
        if not self.enabled:
            return
        alive = []
        for item in list(self.items):
            if item.update():
                alive.append(item)
            else:
                item.dispose()
        self.items = alive
        self._schedule()

    def showScreen(self, x, y, damage, colorRGB, fontSize, alpha, risePixels, lifeTime):
        item = _NativeDamageNumber(self, x, y, damage, colorRGB, fontSize, alpha,
                                   risePixels, lifeTime)
        if item.window is not None:
            self.items.append(item)
            if _pushLog[0] < 30:
                _pushLog[0] += 1
                logger.info('[FlyingDamage] native show screen d=%s x=%.1f y=%.1f items=%d',
                            int(damage), float(x), float(y), len(self.items))

    def showWorld(self, wx, wy, wz, fallbackX, fallbackY, damage, colorRGB,
                  fontSize, alpha, riseMeters, lifeTime):
        item = _NativeDamageNumber(self, fallbackX, fallbackY, damage, colorRGB,
                                   fontSize, alpha, 55.0, lifeTime,
                                   world=(float(wx), float(wy), float(wz)),
                                   riseMeters=riseMeters)
        if item.window is not None:
            self.items.append(item)
            if _pushLog[0] < 30:
                _pushLog[0] += 1
                logger.info('[FlyingDamage] native show world d=%s fallback=(%.1f,%.1f) items=%d',
                            int(damage), float(fallbackX), float(fallbackY), len(self.items))


class Controller(object):

    def __init__(self):
        self._enabled = True
        self._battleMode = False
        self._renderer = _NativeDamageRenderer()

    def init(self):
        logger.info('[FlyingDamage] controller.init begin (native GUI renderer)')
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

        try:
            if g_guiResetters is not None:
                g_guiResetters.add(self._onScreenReset)
        except Exception:
            pass

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
        try:
            if g_guiResetters is not None:
                g_guiResetters.discard(self._onScreenReset)
        except Exception:
            pass
        self._onBattleLeave()
        try:
            from .utils import restore_overrides
            restore_overrides()
        except Exception:
            pass

    def _onScreenReset(self):
        # Active numbers use pixel coordinates captured from current resolution.
        # New numbers will use the new screen size automatically.
        logger.info('[FlyingDamage] screen reset native renderer')

    def _onAvatarReady(self, *a, **kw):
        self._battleMode = True
        _testLog[0] = False
        logger.info('[FlyingDamage] avatar ready -> native renderer active')
        self._renderer.start()
        try:
            from .hooks import setView
            setView(self)
        except Exception:
            pass
        BigWorld.callback(1.0, self._debugTestDamage)
        BigWorld.callback(3.0, self._installSuppressionSafe)

    def _debugTestDamage(self):
        if not self._battleMode or _testLog[0]:
            return
        _testLog[0] = True
        sw, sh = _screen_size()
        logger.info('[FlyingDamage] native debug test at center %.1f %.1f', sw / 2.0, sh / 2.0)
        self.showDamageAt(sw / 2.0, sh / 2.0, 9999, 0x00FFFF, 36, 1.0, 90.0, 5.0)

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
        if not self._battleMode:
            return
        self._renderer.showScreen(x, y, damage, colorRGB, fontSize, alpha, risePixels, lifeTime)

    def showDamageWorld(self, wx, wy, wz, fallbackX, fallbackY, damage, colorRGB,
                        fontSize, alpha, riseMeters=1.35, lifeTime=1.6):
        if not self._battleMode:
            return
        self._renderer.showWorld(wx, wy, wz, fallbackX, fallbackY, damage, colorRGB,
                                 fontSize, alpha, riseMeters, lifeTime)

    def showDamage(self, x, y, damage, colorRGB, fontSize, alpha):
        self.showDamageAt(x, y, damage, colorRGB, fontSize, alpha)


g_controller = Controller()

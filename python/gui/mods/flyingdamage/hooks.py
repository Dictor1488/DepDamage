# -*- coding: utf-8 -*-
# hooks.py  --  Python 2.7
# Damage from onHealthChanged (old-new). Trigger showDamageFromShot.
# World->screen via view-projection matrix (proven method).

import logging

import BigWorld
import GUI
import Math

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_ANCHOR_UP = 2.0
_ctrlRef = [None]
_pendingDamage = {}


def setView(controller):
    _ctrlRef[0] = controller


def resetState():
    _pendingDamage.clear()


def installHooks():
    try:
        from Vehicle import Vehicle
    except Exception:
        logger.error('[FlyingDamage] cannot import Vehicle', exc_info=True)
        return

    @override(Vehicle, 'onHealthChanged')
    def _onHealthChanged(base, self, *args, **kwargs):
        result = base(self, *args, **kwargs)
        try:
            _capture(self, args)
        except Exception:
            logger.error('[FlyingDamage] capture failed', exc_info=True)
        return result

    @override(Vehicle, 'showDamageFromShot')
    def _showDamageFromShot(base, self, *args, **kwargs):
        result = base(self, *args, **kwargs)
        try:
            _emit(self)
        except Exception:
            logger.error('[FlyingDamage] emit failed', exc_info=True)
        return result

    logger.info('[FlyingDamage] hooks installed (view SWF)')


def _capture(vehicle, args):
    vid = getattr(vehicle, 'id', None)
    if vid is None:
        return
    ints = []
    for a in args:
        try:
            ints.append(int(a))
        except (TypeError, ValueError):
            pass
    if len(ints) < 2:
        return
    newH, oldH = ints[0], ints[1]
    if newH < 0:
        newH = 0
    dmg = oldH - newH
    if dmg > 0:
        _pendingDamage[vid] = _pendingDamage.get(vid, 0) + dmg
        _emit(vehicle)


def _buildVP():
    try:
        proj = BigWorld.projection()
        aspect = BigWorld.getAspectRatio()
        m = Math.Matrix()
        m.perspectiveProjection(proj.fov, aspect, proj.nearPlane, proj.farPlane)
        cam = BigWorld.camera()
        if cam is None:
            return None
        m.preMultiply(cam.matrix)
        return m
    except Exception:
        return None


def _project(vehicle):
    vp = _buildVP()
    if vp is None:
        return None
    try:
        tmp = Math.Matrix()
        tmp.set(vehicle.matrix)
        pos = tmp.translation
    except Exception:
        pos = getattr(vehicle, 'position', None)
        if pos is None:
            return None
    v = Math.Vector4(pos.x, pos.y + _ANCHOR_UP, pos.z, 1.0)
    v = vp.applyV4Point(v)
    w = v.w
    if w == 0:
        return None
    visible = w > 0 and -1 <= v.x / w <= 1 and -1 <= v.y / w <= 1
    cx = v.x / w
    cy = v.y / w
    sw, sh = GUI.screenResolution()[:2]
    return ((0.5 + 0.5 * cx) * sw, (0.5 - 0.5 * cy) * sh, visible)


def _emit(vehicle):
    if not g_config.enabled:
        return
    ctrl = _ctrlRef[0]
    if ctrl is None:
        return
    vid = getattr(vehicle, 'id', None)
    if vid is None:
        return
    damage = _pendingDamage.pop(vid, 0)
    if damage <= 0:
        return
    res = _project(vehicle)
    if res is None:
        return
    sx, sy, visible = res
    if not visible:
        return
    logger.info('[FlyingDamage] dmg=%d screen=(%.0f,%.0f)', damage, sx, sy)
    ctrl.showDamage(sx, sy, damage, g_config.colorRGBint,
                    g_config.fontSize, g_config.opacity / 100.0)

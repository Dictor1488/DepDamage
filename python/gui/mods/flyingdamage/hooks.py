# -*- coding: utf-8 -*-
# hooks.py  --  Python 2.7
# Damage from onHealthChanged (old-new). Trigger showDamageFromShot.
# World->screen via view-projection matrix.
# Accumulates damage per vehicle over a short window so simultaneous shells
# (e.g. double-barrel 400+400) merge into ONE number (800), like XVM.

import logging

import BigWorld
import GUI
import Math

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_ANCHOR_UP = 4.5   # meters above tank origin (above the turret)
_MERGE_WINDOW = 0.09   # seconds; damage within this window merges into one number
_ctrlRef = [None]
_pending = {}          # vehicleID -> accumulated damage
_callbacks = {}        # vehicleID -> pending callback id


def setView(controller):
    _ctrlRef[0] = controller


def resetState():
    _pending.clear()
    for cbid in list(_callbacks.values()):
        try:
            BigWorld.cancelCallback(cbid)
        except Exception:
            pass
    _callbacks.clear()


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

    logger.info('[FlyingDamage] hooks installed (merge window)')


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
    if dmg <= 0:
        return

    # attackerID is typically the 3rd int arg. Skip damage dealt by the player.
    if g_config.hideMyDamage and len(ints) >= 3:
        attackerID = ints[2]
        try:
            player = BigWorld.player()
            myID = getattr(player, 'playerVehicleID', None)
            if myID is None:
                myID = getattr(player, 'vehicleID', None)
            if myID is not None and attackerID == myID:
                logger.info('[FlyingDamage] skip my damage dmg=%d (attacker=%d==me)',
                            dmg, attackerID)
                return  # my own damage -> don't show
        except Exception:
            pass

    # Accumulate; schedule a single flush after the merge window.
    _pending[vid] = _pending.get(vid, 0) + dmg
    if vid not in _callbacks:
        _callbacks[vid] = BigWorld.callback(
            _MERGE_WINDOW, lambda: _flush(vid))


def _flush(vid):
    _callbacks.pop(vid, None)
    damage = _pending.pop(vid, 0)
    if damage <= 0:
        return
    if not g_config.enabled:
        return
    ctrl = _ctrlRef[0]
    if ctrl is None:
        return

    vehicle = BigWorld.entity(vid)
    if vehicle is None:
        return

    res = _project(vehicle)
    if res is None:
        return
    sx, sy, visible = res
    # Show even slightly off-screen hits (clamp), skip only if fully behind camera.
    if sx is None or sy is None:
        return

    isEnemy = _isEnemy(vehicle, vid)
    color = g_config.colorForTeam(isEnemy)

    logger.info('[FlyingDamage] dmg=%d screen=(%.0f,%.0f) enemy=%s',
                damage, sx, sy, isEnemy)
    ctrl.showDamage(sx, sy, damage, color,
                    g_config.fontSize, g_config.opacity / 100.0)


def _isEnemy(vehicle, vid):
    """True if target is on the enemy team, False if ally."""
    try:
        player = BigWorld.player()
        myTeam = getattr(player, 'team', None)
        # Try the vehicle's own team attribute first.
        targetTeam = getattr(vehicle, 'team', None)
        if targetTeam is None:
            # Fall back to arena vehicle info.
            arena = getattr(player, 'arena', None)
            if arena is not None:
                info = arena.vehicles.get(vid)
                if info is not None:
                    targetTeam = info.get('team')
        if myTeam is not None and targetTeam is not None:
            return targetTeam != myTeam
    except Exception:
        pass
    # Default to enemy if unknown (most damage is to enemies).
    return True


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
    if w <= 0:
        return None   # truly behind camera
    cx = v.x / w
    cy = v.y / w
    visible = -1 <= cx <= 1 and -1 <= cy <= 1
    sw, sh = GUI.screenResolution()[:2]
    return ((0.5 + 0.5 * cx) * sw, (0.5 - 0.5 * cy) * sh, visible)

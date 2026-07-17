# -*- coding: utf-8 -*-
"""Partial world-space tank following for floating damage numbers.

The number follows a fraction of the damaged tank movement only at the start
of its lifetime, then smoothly detaches. Camera movement is never added as a
screen-space offset; the result is always projected from a world-space point.
"""

import logging

import BigWorld
import Math

from . import hooks

LOG = logging.getLogger('DepDamage')

_PATCHED = False
_ORIGINAL_UPDATE = None
_ORIGINAL_FLUSH_PENDING = None
_ORIGINAL_SPAWN_NUMBER = None

# Follow 45% of tank displacement at spawn and fade that influence to zero
# during the first 55% of the animation.
FOLLOW_STRENGTH = 0.45
FOLLOW_PORTION = 0.55


def _attach_vehicle_to_new_numbers(overlay, vehicleID, before):
    for number in tuple(overlay._numbers):
        if number not in before:
            number._followVehicleID = int(vehicleID)


def _spawn_number(self, point, damage, damageFlag, vehicleID=None):
    before = set(self._numbers)
    result = _ORIGINAL_SPAWN_NUMBER(self, point, damage, damageFlag)
    if vehicleID is not None:
        _attach_vehicle_to_new_numbers(self, vehicleID, before)
    return result


def _flush_pending(self, mergeKey):
    pending = self._pending.pop(mergeKey, None)
    if pending is None or self._closed:
        return
    vehicleID = mergeKey[0]
    self._spawnNumber(
        pending['point'],
        pending['damage'],
        pending['damageFlag'],
        vehicleID
    )


def _current_marker_point(number):
    vehicleID = getattr(number, '_followVehicleID', None)
    overlay = getattr(number, '_overlay', None)
    if vehicleID is None or overlay is None:
        return None

    vehicle = BigWorld.entity(vehicleID)
    if vehicle is None or not getattr(vehicle, 'isStarted', False):
        return None

    try:
        provider = overlay._vehicleMarkerClass.fetchMatrixProvider(vehicle)
        matrix = Math.Matrix()
        matrix.set(provider)
        marker = matrix.translation
        return Math.Vector3(
            marker.x,
            marker.y + overlay.SPAWN_HEIGHT,
            marker.z
        )
    except Exception:
        return None


def _update(self, now):
    if self._disposed:
        return False

    duration = max(0.1, float(self.DURATION))
    progress = (now - self._startTime) / duration
    if progress >= 1.0:
        self.dispose()
        return False
    if progress < 0.0:
        progress = 0.0

    eased = progress * progress * (3.0 - 2.0 * progress)

    baseX = self._worldPoint.x
    baseY = self._worldPoint.y
    baseZ = self._worldPoint.z

    current = _current_marker_point(self)
    if current is not None and progress < FOLLOW_PORTION:
        followProgress = progress / FOLLOW_PORTION
        # Smoothly reduce follow influence so the number does not snap loose.
        detach = followProgress * followProgress * (3.0 - 2.0 * followProgress)
        weight = FOLLOW_STRENGTH * (1.0 - detach)
        baseX += (current.x - self._worldPoint.x) * weight
        baseY += (current.y - self._worldPoint.y) * weight
        baseZ += (current.z - self._worldPoint.z) * weight

    point = Math.Vector3(
        baseX,
        baseY + self.WORLD_RISE * eased,
        baseZ
    )
    projected, visible = self._projector(point)
    if visible:
        import GUI
        screenWidth, screenHeight = GUI.screenResolution()
        x = (0.5 + 0.5 * projected.x) * screenWidth
        y = (0.5 - 0.5 * projected.y) * screenHeight - self.SCREEN_RISE * eased
        self._overlay.updateLabel(self._numberID, x, y, self._alpha(progress), True)
    else:
        self._overlay.updateLabel(self._numberID, 0.0, 0.0, 0.0, False)
    return True


def init():
    global _PATCHED, _ORIGINAL_UPDATE, _ORIGINAL_FLUSH_PENDING, _ORIGINAL_SPAWN_NUMBER
    if _PATCHED:
        return

    _ORIGINAL_UPDATE = hooks._FlashDamageNumber.update
    _ORIGINAL_FLUSH_PENDING = hooks.FlashDamageOverlay._flushPending
    _ORIGINAL_SPAWN_NUMBER = hooks.FlashDamageOverlay._spawnNumber

    hooks._FlashDamageNumber.update = _update
    hooks.FlashDamageOverlay._flushPending = _flush_pending
    hooks.FlashDamageOverlay._spawnNumber = _spawn_number

    _PATCHED = True
    LOG.info('[DepDamage] partial tank-follow motion enabled')


def fini():
    global _PATCHED
    if not _PATCHED:
        return

    hooks._FlashDamageNumber.update = _ORIGINAL_UPDATE
    hooks.FlashDamageOverlay._flushPending = _ORIGINAL_FLUSH_PENDING
    hooks.FlashDamageOverlay._spawnNumber = _ORIGINAL_SPAWN_NUMBER
    _PATCHED = False
    LOG.info('[DepDamage] partial tank-follow motion disabled')

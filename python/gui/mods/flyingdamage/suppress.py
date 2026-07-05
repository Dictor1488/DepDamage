# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# UNIFIED approach (user's idea): intercept _updateHealthMarker (the exact call
# that draws the standard floating damage). From it we:
#   1) compute the damage (previous health - new health for this vehicle),
#   2) feed OUR SWF so our number shows exactly when the game's would,
#   3) suppress the standard number by updating only the health bar via the
#      plain _setHealthMarker setter.
# This guarantees our number appears whenever a standard one would, and the
# standard one never shows.

import sys
import logging

import BigWorld

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]
_SKIP = ('flyingdamage',)
_TARGET = '_updateHealthMarker'

_lastHealth = {}          # vehicleID -> last known health
_feedCallback = [None]    # set by controller: fn(vehicleID, damage)


def setFeed(fn):
    _feedCallback[0] = fn


def resetState():
    _lastHealth.clear()


def installSuppression():
    if _installed[0]:
        return
    for modName in (
        'gui.Scaleform.daapi.view.battle.shared.markers2d.plugins',
        'gui.Scaleform.daapi.view.battle.shared.markers2d.vehicle_plugins',
    ):
        try:
            __import__(modName)
        except Exception:
            pass

    hooked = 0
    done = set()
    for modName, mod in list(sys.modules.items()):
        if mod is None:
            continue
        low = modName.lower()
        if any(s in low for s in _SKIP) or 'marker' not in low:
            continue
        for attr in dir(mod):
            cls = getattr(mod, attr, None)
            if not isinstance(cls, type):
                continue
            if 'VehicleMarkerPlugin' not in [c.__name__ for c in cls.__mro__]:
                continue
            if _TARGET not in cls.__dict__:
                continue
            key = (cls.__module__, cls.__name__)
            if key in done:
                continue
            done.add(key)
            try:
                override(cls, _TARGET, _updateHealthMarkerHook)
                hooked += 1
                logger.info('[FlyingDamage] hooked %s.%s (%s)', attr, _TARGET, modName)
            except Exception:
                logger.info('[FlyingDamage] hook fail %s', attr, exc_info=True)

    logger.info('[FlyingDamage] _updateHealthMarker hooks: %d', hooked)
    if hooked > 0:
        _installed[0] = True


def _updateHealthMarkerHook(base, self, *args, **kwargs):
    # Observed signature: (vehicleID, index, newHealth, aInfo, attackReason, extId)
    try:
        if len(args) >= 3:
            vehID = args[0]
            index = args[1]
            newHealth = args[2]
            reason = args[4] if len(args) >= 5 else None

            # Baseline previous health. On first sight, seed from the vehicle's
            # max health so the first hit isn't lost (delta would be 0).
            if vehID in _lastHealth:
                prev = _lastHealth[vehID]
            else:
                prev = _maxHealth(vehID, newHealth)

            damage = prev - newHealth if isinstance(newHealth, int) else 0
            if damage < 0:
                damage = 0
            _lastHealth[vehID] = newHealth

            if _logN[0] < 15:
                _logN[0] += 1
                logger.info('[FlyingDamage] HM veh=%s new=%s dmg=%s reason=%s',
                            vehID, newHealth, damage, repr(reason))

            # Feed our SWF (controller decides my-damage / color / projection).
            if damage > 0 and _feedCallback[0] is not None:
                try:
                    _feedCallback[0](vehID, damage)
                except Exception:
                    logger.error('[FlyingDamage] feed failed', exc_info=True)

            # Suppress standard number: update only the health bar.
            if g_config.hideStandard:
                setter = getattr(self, '_setHealthMarker', None)
                if setter is not None:
                    return setter(vehID, index, newHealth)
    except Exception:
        logger.error('[FlyingDamage] HM hook error', exc_info=True)

    return base(self, *args, **kwargs)


def _maxHealth(vehID, fallback):
    try:
        import BigWorld
        veh = BigWorld.entity(vehID)
        mh = getattr(veh, 'maxHealth', None)
        if isinstance(mh, int) and mh > 0:
            return mh
    except Exception:
        pass
    return fallback

# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Intercept _updateHealthMarker, feed our AS3 renderer, and optionally suppress
# the standard floating damage number.

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
_feedCallback = [None]    # set by controller: fn(vehicleID, damage, damageType)

_LABELED_TYPES = ('blocked', 'blocked_crit', 'ricochet')


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
            if 'start' in cls.__dict__:
                try:
                    override(cls, 'start', _pluginStartHook)
                    logger.info('[FlyingDamage] hooked %s.start', attr)
                except Exception:
                    pass

    logger.info('[FlyingDamage] _updateHealthMarker hooks: %d', hooked)
    if hooked > 0:
        _installed[0] = True


def _pluginStartHook(base, self, *args, **kwargs):
    result = base(self, *args, **kwargs)
    try:
        from . import g_controller
        g_controller.onMarkerPluginStart()
    except Exception:
        logger.error('[FlyingDamage] onMarkerPluginStart failed', exc_info=True)
    return result


def _updateHealthMarkerHook(base, self, *args, **kwargs):
    # Observed signature: (vehicleID, index, newHealth, aInfo, attackReason, extId)
    try:
        if len(args) >= 3:
            vehID = args[0]
            index = args[1]
            newHealth = args[2]
            reason = args[4] if len(args) >= 5 else None
            damageType = _reasonToDamageType(reason, args, kwargs)

            if vehID in _lastHealth:
                prev = _lastHealth[vehID]
            else:
                prev = _maxHealth(vehID, newHealth)

            damage = prev - newHealth if isinstance(newHealth, int) else 0
            if damage < 0:
                damage = 0
            _lastHealth[vehID] = newHealth

            if _logN[0] < 80:
                _logN[0] += 1
                logger.info('[FlyingDamage] HM veh=%s new=%s dmg=%s reason=%s dtype=%s args=%s',
                            vehID, newHealth, damage, repr(reason), damageType, _compactArgs(args))

            # Feed normal damage and also 0-damage labeled events like BLOCK/RICOCHET
            # if WG sends them through the same marker method.
            if (damage > 0 or damageType in _LABELED_TYPES) and _feedCallback[0] is not None:
                try:
                    _feedCallback[0](vehID, damage, damageType)
                except TypeError:
                    # Backward compatibility with older callback signature.
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


def _reasonToDamageType(reason, args=None, kwargs=None):
    try:
        text = ''
        if reason is not None:
            text = str(reason).lower()
        # Named/enum string cases.
        if 'ricochet' in text:
            return 'ricochet'
        if 'block' in text and 'crit' in text:
            return 'blocked_crit'
        if 'block' in text or 'armor' in text or 'absorbed' in text:
            return 'blocked'
        if 'fire' in text or 'burn' in text:
            return 'fire'
        if 'ram' in text:
            return 'ramming'
        if 'collision' in text:
            return 'world_collision'
        if 'death_zone' in text or 'deathzone' in text:
            return 'death_zone'
        if 'drown' in text or 'water' in text:
            return 'drowning'
        if 'explosion' in text or 'ammo' in text or 'blow' in text:
            return 'explosion'

        # Numeric fallback. These ids can differ between WG versions, so this is
        # intentionally conservative; logs keep reason/args for exact mapping fixes.
        try:
            rid = int(reason)
        except Exception:
            rid = None
        if rid is not None:
            if rid in (2, 16):
                return 'fire'
            if rid in (3, 17):
                return 'ramming'
            if rid in (4, 18):
                return 'world_collision'
            if rid in (5, 19):
                return 'death_zone'
            if rid in (6, 20):
                return 'drowning'
            if rid in (7, 21):
                return 'explosion'
    except Exception:
        pass
    return 'shot'


def _compactArgs(args):
    try:
        out = []
        for a in args[:8]:
            s = repr(a)
            if len(s) > 90:
                s = s[:87] + '...'
            out.append(s)
        return '(' + ', '.join(out) + ')'
    except Exception:
        return '<args>'


def _maxHealth(vehID, fallback):
    try:
        vehicle = BigWorld.entity(vehID)
        if vehicle is not None:
            desc = getattr(vehicle, 'typeDescriptor', None)
            if desc is not None:
                maxH = getattr(desc, 'maxHealth', None)
                if maxH:
                    return int(maxH)
    except Exception:
        pass
    return int(fallback)

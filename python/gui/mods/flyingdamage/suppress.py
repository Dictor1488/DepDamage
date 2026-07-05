# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# The standard floating damage number is drawn by
#   VehicleMarkerPlugin._updateHealthMarker(vehID, idx, health, aInfo, attackReason, damage?)
# The 'shot'/attack-reason argument makes it show the damage text. We wrap it and
# neutralise the damage-text part while keeping the health-bar update, by zeroing
# the "damage" argument (and/or blanking the attack reason) so no number pops up.

import sys
import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]
_SKIP = ('flyingdamage',)
_TARGET = '_updateHealthMarker'


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
    # Observed signature: (vehicleID, index, health, aInfoOr0, reason, damage)
    if _logN[0] < 20:
        _logN[0] += 1
        logger.info('[FlyingDamage] HEALTHMARKER args=%s', repr(args)[:120])

    if not g_config.hideStandard:
        return base(self, *args, **kwargs)

    # Neutralise the damage-text trigger while keeping the health update.
    # The last positional (damage amount) and/or the attack-reason string is what
    # makes the marker pop the number. Zero the damage and blank the reason.
    newArgs = list(args)
    try:
        # blank any string reason like 'shot' / 'fire' / 'ramming'
        for i, a in enumerate(newArgs):
            if isinstance(a, str) and a in ('shot', 'fire', 'world_collision',
                                            'ramming', 'death_zone', 'drowning',
                                            'overturn', 'manual'):
                newArgs[i] = ''
        # zero a trailing integer damage value if present (last arg)
        if newArgs and isinstance(newArgs[-1], int) and newArgs[-1] != 0:
            newArgs[-1] = 0
    except Exception:
        pass
    return base(self, *newArgs, **kwargs)

# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# DIAGNOSTIC 2: trace ALL methods of the vehicle-marker plugin, but only LOG a
# call when its arguments contain an int in the damage range (200..3000). This
# reveals the exact method that carries the standard damage number.

import sys
import logging

from .settings.config import g_config

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]
_MAX_LOG = 80
_SKIP = ('flyingdamage',)


def _looksLikeDamage(args):
    def scan(v, depth=0):
        if depth > 3:
            return False
        if isinstance(v, int) and 150 <= v <= 3200:
            return True
        if isinstance(v, (tuple, list)):
            for x in v:
                if scan(x, depth + 1):
                    return True
        return False
    for a in args:
        if scan(a):
            return True
    return False


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

    traced = 0
    done = set()
    for modName, mod in list(sys.modules.items()):
        if mod is None:
            continue
        low = modName.lower()
        if any(s in low for s in _SKIP):
            continue
        if 'marker' not in low:
            continue
        for attr in dir(mod):
            cls = getattr(mod, attr, None)
            if not isinstance(cls, type):
                continue
            if 'VehicleMarkerPlugin' not in [c.__name__ for c in cls.__mro__]:
                continue
            for mname in list(cls.__dict__.keys()):
                if mname.startswith('__') and mname.endswith('__'):
                    continue
                fn = cls.__dict__.get(mname)
                if not callable(fn):
                    continue
                key = (cls.__name__, mname)
                if key in done:
                    continue
                done.add(key)
                _trace(cls, mname, fn)
                traced += 1

    logger.info('[FlyingDamage] TRACE2 installed on %d methods', traced)
    if traced > 0:
        _installed[0] = True


def _trace(cls, mname, original):
    def wrapper(self, *args, **kwargs):
        if _logN[0] < _MAX_LOG and _looksLikeDamage(args):
            _logN[0] += 1
            logger.info('[FlyingDamage] DMGCALL %s.%s args=%s',
                        type(self).__name__, mname, repr(args)[:120])
        return original(self, *args, **kwargs)
    try:
        setattr(cls, mname, wrapper)
    except Exception:
        pass

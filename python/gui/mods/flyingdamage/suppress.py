# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# DIAGNOSTIC MODE: trace every method call on the vehicle-marker plugin that
# has "damage"/"invoke"/"marker" in its name, so we can see EXACTLY which call
# renders the standard floating damage number when a hit lands.

import sys
import logging

from .settings.config import g_config

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]
_MAX_LOG = 120

_TRACE_HINTS = ('damage', 'invoke', 'showmarker', 'updatemarker', 'setmarker',
                'addmarker', 'icon')
_SKIP = ('flyingdamage',)


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
                ml = mname.lower()
                if not any(h in ml for h in _TRACE_HINTS):
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

    logger.info('[FlyingDamage] TRACE installed on %d methods', traced)
    if traced > 0:
        _installed[0] = True


def _trace(cls, mname, original):
    def wrapper(self, *args, **kwargs):
        if _logN[0] < _MAX_LOG:
            _logN[0] += 1
            logger.info('[FlyingDamage] CALL %s.%s args=%s',
                        type(self).__name__, mname, repr(args)[:90])
        # Suppress if this looks like the damage-number renderer AND hideStandard.
        if g_config.hideStandard and 'damage' in mname.lower() and 'icon' in mname.lower():
            if _logN[0] < _MAX_LOG:
                logger.info('[FlyingDamage] -> SUPPRESSED %s', mname)
            return None
        return original(self, *args, **kwargs)
    try:
        setattr(cls, mname, wrapper)
    except Exception:
        pass

# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# The standard damage number is drawn by VehicleMarkerPlugin.__showDamageIcon
# (mangled: _VehicleMarkerPlugin__showDamageIcon). The actual runtime class is a
# subclass (e.g. VehicleMarkerTargetPluginReplayPlaying). We hook that mangled
# method on the BASE class where it is defined AND on every loaded subclass,
# because name-mangled lookups resolve on the instance's own class dict.

import sys
import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_installed = [False]
_logN = [0]

_MANGLED = '_VehicleMarkerPlugin__showDamageIcon'
_SKIP = ('flyingdamage',)


def installSuppression():
    if _installed[0]:
        return
    if not g_config.hideStandard:
        return

    # Ensure the plugin module is loaded.
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

    # Walk all loaded modules; hook the mangled method on ANY class that has it
    # in its own __dict__ (base + every subclass that redefines/carries it).
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
            # Hook on classes that define the mangled method in their own dict.
            if _MANGLED in cls.__dict__:
                key = (cls.__module__, cls.__name__)
                if key in done:
                    continue
                done.add(key)
                try:
                    override(cls, _MANGLED, _suppressed)
                    hooked += 1
                    logger.info('[FlyingDamage] hooked %s.%s', attr, modName)
                except Exception:
                    logger.info('[FlyingDamage] hook fail %s', attr, exc_info=True)

    logger.info('[FlyingDamage] __showDamageIcon hooks: %d', hooked)
    if hooked > 0:
        _installed[0] = True


def _suppressed(base, self, *args, **kwargs):
    if _logN[0] < 15:
        _logN[0] += 1
        logger.info('[FlyingDamage] __showDamageIcon SUPPRESSED cls=%s',
                    type(self).__name__)
    if g_config.hideStandard:
        return None
    return base(self, *args, **kwargs)

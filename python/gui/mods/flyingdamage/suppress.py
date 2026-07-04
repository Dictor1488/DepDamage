# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Suppress the game's standard floating damage. XVM shows it is drawn by the
# vehicle marker (net.wg.gui.battle.views.vehicleMarkers.VehicleMarker), driven
# from the markers2d plugins we DID find in this client:
#   VehicleMarkerTargetPlugin, MarkerPlugin
# We hook the plugin method that pushes the damage number to the marker SWF and
# no-op it. Names vary, so we scan the known plugin classes and log methods.

import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

_PLUGIN_MODULE = 'gui.Scaleform.daapi.view.battle.shared.markers2d.plugins'
_PLUGIN_CLASSES = [
    'VehicleMarkerTargetPlugin',
    'VehicleMarkerTargetPluginReplayPlaying',
    'MarkerPlugin',
]

# Method fragments that invoke the marker's damage display (as_* -> flash).
_METHOD_HINTS = [
    'showdamage', 'updatehealth', 'senddamage', 'damageicon',
    'as_showdamage', 'as_updatehealth', '__updatevehiclehealth',
    'updatevehiclehealth', 'onvehiclehealthchanged', '_hpchanged',
]


def installSuppression():
    if not g_config.hideStandard:
        logger.info('[FlyingDamage] suppression disabled')
        return

    try:
        mod = __import__(_PLUGIN_MODULE, fromlist=['*'])
    except Exception:
        logger.error('[FlyingDamage] cannot import markers2d.plugins', exc_info=True)
        return

    hooked = 0
    for clsName in _PLUGIN_CLASSES:
        cls = getattr(mod, clsName, None)
        if not isinstance(cls, type):
            continue
        # Log all methods once, so we can pinpoint if hints miss.
        allMethods = [m for m in dir(cls) if not m.startswith('__init__')]
        damageish = [m for m in allMethods
                     if 'amage' in m.lower() or 'health' in m.lower()]
        logger.info('[FlyingDamage] %s damage/health methods: %s',
                    clsName, damageish)

        for m in allMethods:
            ml = m.lower()
            if any(h in ml for h in _METHOD_HINTS):
                try:
                    def _suppressed(base, self, *a, **k):
                        if g_config.hideStandard:
                            return None
                        return base(self, *a, **k)
                    override(cls, m, _suppressed)
                    hooked += 1
                    logger.info('[FlyingDamage] suppressed %s.%s', clsName, m)
                except Exception:
                    logger.info('[FlyingDamage] suppress fail %s.%s', clsName, m,
                                exc_info=True)

    if hooked == 0:
        logger.warning('[FlyingDamage] no method suppressed; see method lists above')
    else:
        logger.info('[FlyingDamage] suppression active (%d hooks)', hooked)

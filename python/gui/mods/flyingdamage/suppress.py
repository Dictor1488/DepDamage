# -*- coding: utf-8 -*-
# suppress.py  --  Python 2.7
# Suppresses the game's standard floating damage. In this client the numbers are
# drawn by battleDamageIndicatorApp.swf, driven by a Python damage-indicator
# controller. We hook that controller's "show damage" method.

import logging

from .utils import override
from .settings.config import g_config

logger = logging.getLogger(__name__)

# Known module paths for the damage indicator controller across versions.
_MODULE_CANDIDATES = [
    'gui.Scaleform.daapi.view.battle.shared.damage_indicator',
    'gui.Scaleform.daapi.view.battle.shared.damageIndicator',
    'gui.battle_control.controllers.damage_indicator_ctrl',
    'gui.Scaleform.daapi.view.battle.classic.damage_indicator',
]

# Method names on the controller / panel that emit the floating damage number.
_METHOD_CANDIDATES = [
    '_DamageIndicator__showDamageIcon',
    '_showDamageIcon',
    'showDamageIcon',
    '_addDamageIndicator',
    'addDamageIndicator',
    '_updateDamageIndicator',
    'as_showDamageIconS',
]


def installSuppression():
    if not g_config.hideStandard:
        logger.info('[FlyingDamage] standard suppression disabled')
        return

    hooked = 0
    found_classes = []

    for modName in _MODULE_CANDIDATES:
        try:
            mod = __import__(modName, fromlist=['*'])
        except Exception:
            continue
        # Find classes that look like the damage indicator.
        for attr in dir(mod):
            if 'amageIndicator' not in attr and 'amage_indicator' not in attr:
                continue
            cls = getattr(mod, attr, None)
            if not isinstance(cls, type):
                continue
            found_classes.append('%s.%s' % (modName, attr))
            for methodName in _METHOD_CANDIDATES:
                if hasattr(cls, methodName):
                    try:
                        def _suppressed(base, self, *args, **kwargs):
                            if g_config.hideStandard:
                                return None
                            return base(self, *args, **kwargs)
                        override(cls, methodName, _suppressed)
                        hooked += 1
                        logger.info('[FlyingDamage] suppressed standard: %s.%s',
                                    attr, methodName)
                    except Exception:
                        logger.info('[FlyingDamage] suppress failed %s.%s',
                                    attr, methodName, exc_info=True)

    if hooked == 0:
        logger.warning('[FlyingDamage] standard damage NOT suppressed. '
                       'Candidate classes found: %s', found_classes)
        _dumpDamageIndicator(found_classes)
    else:
        logger.info('[FlyingDamage] standard damage suppression active (%d hooks)',
                    hooked)


def _dumpDamageIndicator(found_classes):
    """Log methods of any damage-indicator-looking class we located."""
    for modName in _MODULE_CANDIDATES:
        try:
            mod = __import__(modName, fromlist=['*'])
        except Exception:
            continue
        for attr in dir(mod):
            if 'amageIndicator' in attr or 'amage_indicator' in attr:
                cls = getattr(mod, attr, None)
                if isinstance(cls, type):
                    methods = [m for m in dir(cls) if 'amage' in m or 'how' in m]
                    logger.warning('[FlyingDamage] %s.%s methods(damage/show): %s',
                                   modName, attr, methods)

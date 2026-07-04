# -*- coding: utf-8 -*-
# settings/config.py  --  Python 2.7
# In-game settings via ModsSettingsAPI: enabled + text size + text color + opacity.

import logging

logger = logging.getLogger(__name__)

MOD_LINKAGE = 'com.author.flyingdamage'
MOD_DISPLAY_NAME = u'Flying Damage'

COLOR_PRESETS = [
    (u'White',  (255, 255, 255)),
    (u'Yellow', (255, 220, 60)),
    (u'Orange', (255, 150, 40)),
    (u'Red',    (255, 70, 70)),
    (u'Green',  (120, 255, 120)),
    (u'Cyan',   (90, 220, 255)),
]


class Config(object):

    def __init__(self):
        self.enabled = True
        self.fontSize = 24
        self.colorIndex = 1   # Yellow
        self.opacity = 100
        self.hideStandard = True
        self.hideMyDamage = True

    @property
    def colorRGB(self):
        idx = self.colorIndex
        if idx < 0 or idx >= len(COLOR_PRESETS):
            idx = 0
        return COLOR_PRESETS[idx][1]

    @property
    def colorRGBint(self):
        r, g, b = self.colorRGB
        return (r << 16) | (g << 8) | b

    def registerSettings(self):
        try:
            from gui.modsSettingsApi import g_modsSettingsApi
        except ImportError:
            logger.warning('[FlyingDamage] ModsSettingsAPI not found; defaults used.')
            return
        template = self._template()
        saved = g_modsSettingsApi.setModTemplate(
            MOD_LINKAGE, template, self._onChanged)
        if saved is not None:
            self._apply(saved)

    def _template(self):
        colorLabels = [lbl for (lbl, _rgb) in COLOR_PRESETS]
        return {
            'modDisplayName': MOD_DISPLAY_NAME,
            'enabled': self.enabled,
            'column1': [
                {'type': 'Slider', 'text': u'Text size',
                 'value': self.fontSize, 'minimum': 12, 'maximum': 48,
                 'step': 1, 'format': u'{{value}} px', 'varName': 'fontSize'},
                {'type': 'Dropdown', 'text': u'Text color',
                 'value': self.colorIndex,
                 'options': [{'label': l} for l in colorLabels],
                 'varName': 'colorIndex'},
            ],
            'column2': [
                {'type': 'CheckBox', 'text': u'Hide standard damage',
                 'value': self.hideStandard, 'varName': 'hideStandard'},
                {'type': 'CheckBox', 'text': u'Hide my own damage',
                 'value': self.hideMyDamage, 'varName': 'hideMyDamage'},
                {'type': 'Slider', 'text': u'Opacity',
                 'value': self.opacity, 'minimum': 0, 'maximum': 100,
                 'step': 5, 'format': u'{{value}} %', 'varName': 'opacity'},
            ],
        }

    def _onChanged(self, linkage, newSettings):
        if linkage == MOD_LINKAGE:
            self._apply(newSettings)

    def _apply(self, s):
        try:
            self.enabled = bool(s.get('enabled', self.enabled))
            self.fontSize = int(s.get('fontSize', self.fontSize))
            self.colorIndex = int(s.get('colorIndex', self.colorIndex))
            self.opacity = int(s.get('opacity', self.opacity))
            self.hideStandard = bool(s.get('hideStandard', self.hideStandard))
            self.hideMyDamage = bool(s.get('hideMyDamage', self.hideMyDamage))
        except Exception:
            logger.error('[FlyingDamage] apply settings failed', exc_info=True)


g_config = Config()

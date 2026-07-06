# -*- coding: utf-8 -*-
# settings/config.py  --  Python 2.7
# In-game settings via ModsSettingsAPI.

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


def _rgbToInt(rgb):
    r, g, b = rgb
    return (r << 16) | (g << 8) | b


class Config(object):

    def __init__(self):
        self.enabled = True
        self.fontSize = 24
        self.opacity = 100
        self.hideStandard = True
        self.hideMyDamage = True

        # Marker-layer renderer needs a real world anchor because it renders in
        # the same world-bound marker canvas as tank HP/name markers.
        self.anchorMode = 'world_anchor'
        self.risePixels = 55
        self.riseMeters = 1.35
        self.lifeTime = 1.6

        self.colorByTeam = True
        self.colorIndex = 1          # fallback single color (Yellow)
        self.enemyColorIndex = 3     # Red
        self.allyColorIndex = 4      # Green

    def _presetInt(self, idx):
        if idx < 0 or idx >= len(COLOR_PRESETS):
            idx = 0
        return _rgbToInt(COLOR_PRESETS[idx][1])

    @property
    def colorRGBint(self):
        return self._presetInt(self.colorIndex)

    @property
    def enemyColorInt(self):
        return self._presetInt(self.enemyColorIndex)

    @property
    def allyColorInt(self):
        return self._presetInt(self.allyColorIndex)

    def colorForTeam(self, isEnemy):
        if not self.colorByTeam:
            return self.colorRGBint
        return self.enemyColorInt if isEnemy else self.allyColorInt

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

        def dropdown(text, value, varName):
            return {'type': 'Dropdown', 'text': text, 'value': value,
                    'options': [{'label': l} for l in colorLabels],
                    'varName': varName}

        return {
            'modDisplayName': MOD_DISPLAY_NAME,
            'enabled': self.enabled,
            'column1': [
                {'type': 'Slider', 'text': u'Text size',
                 'value': self.fontSize, 'minimum': 12, 'maximum': 48,
                 'step': 1, 'format': u'{{value}} px', 'varName': 'fontSize'},
                {'type': 'CheckBox', 'text': u'Color by team (enemy/ally)',
                 'value': self.colorByTeam, 'varName': 'colorByTeam'},
                dropdown(u'Enemy color', self.enemyColorIndex, 'enemyColorIndex'),
                dropdown(u'Ally color', self.allyColorIndex, 'allyColorIndex'),
                dropdown(u'Single color (if not by team)',
                         self.colorIndex, 'colorIndex'),
                {'type': 'Label', 'text': u'Render mode: battle vehicle marker layer'},
            ],
            'column2': [
                {'type': 'Slider', 'text': u'Opacity',
                 'value': self.opacity, 'minimum': 0, 'maximum': 100,
                 'step': 5, 'format': u'{{value}} %', 'varName': 'opacity'},
                {'type': 'CheckBox', 'text': u'Hide standard damage',
                 'value': self.hideStandard, 'varName': 'hideStandard'},
                {'type': 'CheckBox', 'text': u'Hide my own damage',
                 'value': self.hideMyDamage, 'varName': 'hideMyDamage'},
                {'type': 'Slider', 'text': u'Rise height',
                 'value': self.riseMeters, 'minimum': 0.4, 'maximum': 3.0,
                 'step': 0.05, 'format': u'{{value}} m', 'varName': 'riseMeters'},
                {'type': 'Slider', 'text': u'Lifetime',
                 'value': self.lifeTime, 'minimum': 0.6, 'maximum': 3.0,
                 'step': 0.1, 'format': u'{{value}} s', 'varName': 'lifeTime'},
            ],
        }

    def _onChanged(self, linkage, newSettings):
        if linkage == MOD_LINKAGE:
            self._apply(newSettings)

    def _apply(self, s):
        try:
            self.enabled = bool(s.get('enabled', self.enabled))
            self.fontSize = int(s.get('fontSize', self.fontSize))
            self.opacity = int(s.get('opacity', self.opacity))
            self.hideStandard = bool(s.get('hideStandard', self.hideStandard))
            self.hideMyDamage = bool(s.get('hideMyDamage', self.hideMyDamage))
            self.colorByTeam = bool(s.get('colorByTeam', self.colorByTeam))
            self.colorIndex = int(s.get('colorIndex', self.colorIndex))
            self.enemyColorIndex = int(s.get('enemyColorIndex', self.enemyColorIndex))
            self.allyColorIndex = int(s.get('allyColorIndex', self.allyColorIndex))

            # Ignore any old saved screen_fixed setting. The new renderer is
            # bound to vehicle-marker world matrices only.
            self.anchorMode = 'world_anchor'

            self.riseMeters = float(s.get('riseMeters', self.riseMeters))
            self.lifeTime = float(s.get('lifeTime', self.lifeTime))
            self.risePixels = int(max(20, min(160, self.riseMeters * 42.0)))
        except Exception:
            logger.error('[FlyingDamage] apply settings failed', exc_info=True)


g_config = Config()

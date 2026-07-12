# -*- coding: utf-8 -*-
"""Standalone screen-space floating damage application."""

import logging

import BigWorld
import GUI
import Math
import SCALEFORM

from gui import DEPTH_OF_VehicleMarker
from gui.Scaleform.daapi.view.external_components import ExternalFlashComponent, ExternalFlashSettings
from gui.Scaleform.flash_wrapper import InputKeyMode
from gui.Scaleform.framework.entities.BaseDAAPIModule import BaseDAAPIModule

LOG = logging.getLogger('DepDamage')


class DepDamageFlashMeta(BaseDAAPIModule):

    def as_showDamage(self, screenWidth, screenHeight, x, y, damage, attackerID, damageType, damageFlag):
        if self._isDAAPIInited():
            return self.flashObject.as_showDamage(
                screenWidth, screenHeight, x, y, damage, attackerID, damageType, damageFlag
            )


class DepDamageFlash(ExternalFlashComponent, DepDamageFlashMeta):

    def __init__(self, vehicleMarkerClass):
        super(DepDamageFlash, self).__init__(
            ExternalFlashSettings('DepDamageFlash', 'DepDamageFlash.swf', 'root', None)
        )
        self._vehicleMarkerClass = vehicleMarkerClass
        self._viewProjection = Math.Matrix()
        self._tempMatrix = Math.Matrix()

        self.createExternalComponent()
        self.movie.backgroundAlpha = 0.0
        self.movie.scaleMode = SCALEFORM.eMovieScaleMode.NO_SCALE
        self.component.wg_inputKeyMode = InputKeyMode.NO_HANDLE
        self.component.position.z = DEPTH_OF_VehicleMarker - 0.01
        self.component.focus = False
        self.component.moveFocus = False
        self.active(True)

    def showDamage(self, vehicleID, damage, attackerID, damageType, damageFlag):
        try:
            vehicle = BigWorld.entity(vehicleID)
            if vehicle is None or not getattr(vehicle, 'isStarted', False):
                return False

            provider = self._vehicleMarkerClass.fetchMatrixProvider(vehicle)
            self._tempMatrix.set(provider)
            point = self._tempMatrix.translation
            projected, visible = self._projectPoint(point)
            if not visible:
                return False

            screenWidth, screenHeight = GUI.screenResolution()
            x = (0.5 + 0.5 * projected.x) * screenWidth
            y = (0.5 - 0.5 * projected.y) * screenHeight
            self.as_showDamage(
                screenWidth, screenHeight, x, y,
                damage, attackerID, damageType, damageFlag
            )
            return True
        except Exception:
            LOG.exception('[DepDamage] failed to project/show damage')
            return False

    def _projectPoint(self, point):
        camera = BigWorld.camera()
        if camera is None:
            return Math.Vector4(), False

        projection = BigWorld.projection()
        self._viewProjection.perspectiveProjection(
            projection.fov,
            BigWorld.getAspectRatio(),
            projection.nearPlane,
            projection.farPlane
        )
        self._viewProjection.preMultiply(camera.matrix)

        clip = Math.Vector4(point.x, point.y, point.z, 1)
        clip = self._viewProjection.applyV4Point(clip)
        visible = (
            point.lengthSquared != 0.0 and
            clip.w > 0 and
            -1 <= clip.x / clip.w <= 1 and
            -1 <= clip.y / clip.w <= 1
        )
        if clip.w != 0:
            clip = clip.scale(1.0 / clip.w)
        return clip, visible

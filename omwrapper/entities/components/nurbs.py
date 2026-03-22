from __future__ import annotations

from maya.api import OpenMaya as om

from omwrapper.entities.components.base import Component1D, ComponentPoint, recycle_mit, Component2D


class CurveCV(Component1D, ComponentPoint):
    _mit_class = om.MItCurveCV
    _mfn_constant = om.MFn.kCurveCVComponent
    _name = '.cv'
    @recycle_mit
    def _post_set_positions(self, *args, mit:om.MItCurveCV=None, **kwargs):
        mit.updateCurve()

class SurfaceCV(Component2D, ComponentPoint):
    _mit_class = om.MItSurfaceCV
    _mfn_constant = om.MFn.kSurfaceCVComponent
    _name = '.cv'
    @recycle_mit
    def _post_set_positions(self, *args, mit:om.MItSurfaceCV=None, **kwargs):
        mit.updateSurface()
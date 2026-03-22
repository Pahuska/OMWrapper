from __future__ import annotations

from maya.api import OpenMaya as om

from omwrapper.entities.components.base import Component3D, ComponentPoint


class LatticePoint(Component3D, ComponentPoint):
    _mfn_constant = om.MFn.kLatticeComponent
    _name = '.pt'


from maya.api import OpenMaya as om

from omwrapper.entities.attributes.base import QuantifiableAttribute


class NumericAttribute(QuantifiableAttribute):
    _mfn_class = om.MFnNumericAttribute
    _mfn_constant = om.MFn.kNumericAttribute


class UnitAttribute(QuantifiableAttribute):
    _mfn_class = om.MFnUnitAttribute
    _mfn_constant = om.MFn.kUnitAttribute
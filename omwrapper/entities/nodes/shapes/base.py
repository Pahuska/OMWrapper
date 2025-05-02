from typing import Union, Iterable

from maya.api import OpenMaya as om

from omwrapper.entities.nodes.dag import DagNode


class GeometryShape(DagNode):
    ...


TPointsSequence = Union[Iterable[Union[om.MPoint, om.MFloatPoint]], om.MPointArray]

from __future__ import annotations

import json
from typing import Union, Iterable, TYPE_CHECKING, Sequence

from maya.api import OpenMaya as om

from omwrapper.api import apiundo
from omwrapper.api.modifiers.maya import DagModifier
from omwrapper.constants import DataType
from omwrapper.entities.base import recycle_mfn, undoable_proxy_wrap
from omwrapper.entities.nodes.shapes.base import GeometryShape, TPointsSequence

TKNotsSequence = Union[om.MDoubleArray, Iterable[float]]

if TYPE_CHECKING:
    from omwrapper.entities.nodes.transform import Transform

class NurbsCurve(GeometryShape):
    _mfn_class = om.MFnNurbsCurve
    _mfn_constant = om.MFn.kNurbsCurve

    def api_mfn(self) -> om.MFnNurbsCurve:
        return super().api_mfn()

    @classmethod
    def create_(cls, cvs:TPointsSequence, knots:TKNotsSequence, degree:int, form:int, is_2d:bool, rational:bool,
                parent:Union[om.MObject, Transform]=om.MObject.kNullObj) -> Union["NurbsCurve", "Transform"]:
        """
        Create a curve based on the control vertices and knots provided

        Args:
            cvs (TPointsSequence): positions of the controls vertices
            knots (TKNotsSequence): parameter values of the knots. There must be (# spans + 2*degree - 1) knots provided,
             and they must appear in non-decreasing order.
            degree (int):
            form (int):
            is_2d (bool):
            rational (bool):
            parent (MObject, Transform, optional):

        Returns:
            (NurbsCurve, DagNode): if the parent is not specified, a new transform will be created and returned. Otherwise
             the new NurbsCurve itself will be returned
        """

        if hasattr(parent, 'api_mobject'):
            parent = parent.api_mobject()

        mfn = cls._mfn_class()
        obj = mfn.create(cvs, knots, degree, form, is_2d, rational, parent)
        return cls._factory(MObject=obj)

    @classmethod
    def create(cls, cvs:TPointsSequence, knots:TKNotsSequence, degree:int, form:int, is_2d:bool, rational:bool,
                parent:Union[om.MObject, Transform]=om.MObject.kNullObj, name:str=None) -> Union["NurbsCurve", "Transform"]:

        if hasattr(parent, 'api_mobject'):
            parent = parent.api_mobject()

        modifier = DagModifier()
        curve = modifier.create_node('nurbsCurve', name=name, parent=parent)
        modifier.doIt()

        curve = cls._factory(MObject=curve)

        plug = curve.attr('create').api_mplug()

        data = om.MFnNurbsCurveData().create()
        mfn = cls._mfn_class()
        mfn.create(cvs, knots, degree, form, is_2d, rational, parent)

        edit_mod = DagModifier()
        edit_mod.set_plug_value(plug, data)
        edit_mod.doIt()

        apiundo.commit(undo=modifier.undoIt, redo=modifier.doIt)
        return curve

    @recycle_mfn
    def update(self, mfn:om.MFnNurbsCurve=None):
        mfn.updateCurve()

    @recycle_mfn
    def get_point(self, index: int, space: int = om.MSpace.kObject, mfn: om.MFnNurbsCurve = None) -> om.MPoint:
        """
        Query the position of a ControlVertex
        Args:
            index (int): the index of the ControlVertex to query
            space (MSpace, optional): the space in which the point is to be returned. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            MPoint: the position of the vertex in the required space

        """
        return mfn.cvPosition(index, space=space)

    @recycle_mfn
    def set_point_(self, point: om.MPoint, index: int, space: int = om.MSpace.kObject, mfn: om.MFnNurbsCurve = None):
        """
        [NOT UNDOABLE]
        Set the position of a ControlVertex

        Args:
            point (MPoint): the new coordinates of the point
            index (int): the index of the ControlVertex to query
            space (MSpace, optional): the space in which the point is specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        mfn.setCVPosition(index, point, space=space)
        mfn.updateCurve()

    @recycle_mfn
    @undoable_proxy_wrap(get_point, set_point_)
    def set_point(self, point: om.MPoint, index: int, space: int = om.MSpace.kObject, mfn: om.MFnNurbsCurve = None):
        """
        [UNDOABLE]
        Set the position of a ControlVertex

        Args:
            point (MPoint): the new coordinates of the point
            index (int): the index of the ControlVertex to query
            space (MSpace, optional): the space in which the point is specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        ...

    @recycle_mfn
    def get_points(self, space: int = om.MSpace.kObject, mfn: om.MFnNurbsCurve = None) -> om.MPointArray:
        """
        Query the position of all ControlVertices
        Args:
            space (MSpace, optional): the space in which the point is to be returned. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            MPoint: the position of the vertex in the required space

        """
        return mfn.cvPositions(space=space)

    @recycle_mfn
    def set_points_(self, points: TPointsSequence, space: int = om.MSpace.kObject, mfn: om.MFnNurbsCurve = None):
        """
        [NOT UNDOABLE]
        Set the position of all ControlVertices

        Args:
            points (TPointsSequence): the new coordinates of the point
            space (MSpace, optional): the space in which the points are specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        mfn.setCVPositions(points, space=space)
        mfn.updateCurve()


    @recycle_mfn
    @undoable_proxy_wrap(get_points, set_points_)
    def set_points(self, points: TPointsSequence, space: int = om.MSpace.kObject, mfn: om.MFnNurbsCurve = None):
        """
        [UNDOABLE]
        Set the position of all ControlVertices

        Args:
            points (TPointsSequence): the new coordinates of the point
            space (MSpace, optional): the space in which the points are specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        ...

    @recycle_mfn
    def get_param_at_point(self, point:Union[om.MPoint(), Iterable[float]], tolerance:float=0.001,
                           space:int=om.MSpace.kObject, mfn:om.MFnNurbsCurve=None) -> float:
        """
        Find the parameter at the given point on the curve.

        Args:
            point (MPoint, list): a point on the curve
            tolerance (float, optional): the max distance the point can be from the curve and be considered to lie on it.
             Defaults to 0.001
            space (MSpace, optional): the space in which the point is specified. Defaults to kObject
            mfn (MFnNurbsCurve, optional): a function set representing the curve

        Returns:
            float: the curve parameter at the given point

        """
        point = DataType.to_point(point)
        return mfn.getParamAtPoint(point, tolerance=tolerance, space=space)

    @recycle_mfn
    def get_point_at_param(self, param: float, space: int = om.MSpace.kObject, mfn:om.MFnNurbsCurve=None) -> om.MPoint:
        """
        Get the point at the given curve parameter.

        Args:
            param (float): The parameter at which to find the point.
            space (MSpace, optional): The space in which the point is to be returned. Defaults to kObject
            mfn (MFnNurbsCurve, optional): a function set representing the curve

        Returns:
            MPoint: the point at the given parameter in the required space

        """
        return mfn.getParamAtPoint(param, space=space)

    @recycle_mfn
    def find_param_from_length(self, length:float, mfn:om.MFnNurbsCurve=None) -> float:
        """
        Get the parameter value at the given length. If the parameter cannot be determined, then the value at the end
        point of the curve is returned

        Args:
            length (float): a distance along the curve
            mfn (MFnNurbsCurve, optional): a function set representing the curve

        Returns:
            float: the parameter at the given length

        """
        return mfn.findParamFromLength(length)

    @recycle_mfn
    def find_length_from_param(self, param: float, mfn: om.MFnNurbsCurve = None) -> float:
        """
        Get the length at the given parameter. If the length cannot be determined, then a distance of 0.0 is returned.

        Args:
            param (float): a parameter value on the curve
            mfn (MFnNurbsCurve, optional): a function set representing the curve

        Returns:
            float: the parameter at the given length

        """
        return mfn.findParamFromLength(param)

    @property
    def form(self):
        return self.api_mfn().form

    @property
    def degree(self):
        return self.api_mfn().degree

    @property
    def is_open(self):
        mfn = self.api_mfn()
        return mfn.form == mfn.kOpen

    @property
    def is_closed(self):
        mfn = self.api_mfn()
        return mfn.form == mfn.kClosed

    @property
    def is_periodic(self):
        mfn = self.api_mfn()
        return mfn.form == mfn.kPeriodic

    @property
    def cv_count(self):
        return self.api_mfn().numCVs

    @property
    def knot_count(self):
        return self.api_mfn().numKnots

    @property
    def span_count(self):
        return self.api_mfn().numSpans

    @property
    def knot_domain(self):
        return self.api_mfn().knotDomain

    @recycle_mfn
    def get_curve_data(self, space:int=om.MSpace.kObject, mfn: om.MFnNurbsCurve = None) -> dict:
        data = {'degree':mfn.degree,
                'form':mfn.form,
                'cvs':mfn.cvPositions(space=space),
                'knots':mfn.knots()}
        return data

    @recycle_mfn
    def get_json_curve_data(self, space:int=om.MSpace.kObject, mfn: om.MFnNurbsCurve = None) -> str:
        data = self.get_curve_data(space=space, mfn=mfn)
        data['cvs'] = [(p.x, p.y, p.z) for p in data['cvs']]
        data['knots'] = list(data['knots'])
        return json.dumps(data, sort_keys=True, indent=4)

class NurbsSurface(GeometryShape):
    _mfn_class = om.MFnNurbsSurface
    _mfn_constant = om.MFn.kNurbsSurface

    def api_mfn(self) -> om.MFnNurbsSurface:
        return super().api_mfn()

    @classmethod
    def create_(cls, *args, **kwargs) -> None:
        raise NotImplementedError('Mesh.create_ is not implemented yet')

    @classmethod
    def create(cls, *args, **kwargs) -> None:
        raise NotImplementedError('Mesh.create is not implemented yet')

    @recycle_mfn
    def update(self, mfn: om.MFnNurbsSurface = None):
        mfn.updateSurface()

    @recycle_mfn
    def get_point(self, index: Sequence[int], space: int = om.MSpace.kObject, mfn: om.MFnNurbsSurface = None) -> om.MPoint:
        """
        Query the position of a ControlVertex
        Args:
            index (list, tuple): the [u,v] indices of the ControlVertex to query
            space (MSpace, optional): the space in which the point is to be returned. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            MPoint: the position of the vertex in the required space

        """
        u, v = index
        return mfn.cvPosition(u, v, space=space)

    @recycle_mfn
    def set_point_(self, point: om.MPoint, index: Sequence[int], space: int = om.MSpace.kObject, mfn: om.MFnNurbsSurface = None):
        """
        [NOT UNDOABLE]
        Set the position of a ControlVertex

        Args:
            point (MPoint): the new coordinates of the point
            index (int): the [u,v] indices of the ControlVertex to query
            space (MSpace, optional): the space in which the point is specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        u, v = index
        mfn.setCVPosition(index, point, space=space)
        mfn.updateSurface()

    @recycle_mfn
    @undoable_proxy_wrap(get_point, set_point_)
    def set_point(self, point: om.MPoint, index: Sequence[int], space: int = om.MSpace.kObject, mfn: om.MFnNurbsSurface = None):
        """
        [UNDOABLE]
        Set the position of a ControlVertex

        Args:
            point (MPoint): the new coordinates of the point
            index (int): the [u,v] indices of the ControlVertex to query
            space (MSpace, optional): the space in which the point is specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        ...

    @recycle_mfn
    def get_points(self, space: int = om.MSpace.kObject, mfn: om.MFnNurbsSurface = None) -> om.MPointArray:
        """
        Query the position of all ControlVertices
        Args:
            space (MSpace, optional): the space in which the point is to be returned. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            MPoint: the position of the vertex in the required space

        """
        return mfn.cvPositions(space=space)

    @recycle_mfn
    def set_points_(self, points: TPointsSequence, space: int = om.MSpace.kObject, mfn: om.MFnNurbsSurface = None):
        """
        [NOT UNDOABLE]
        Set the position of all ControlVertices

        Args:
            points (TPointsSequence): the new coordinates of the point
            space (MSpace, optional): the space in which the points are specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        mfn.setCVPositions(points, space=space)
        mfn.updateSurface()

    @recycle_mfn
    @undoable_proxy_wrap(get_points, set_points_)
    def set_points(self, points: TPointsSequence, space: int = om.MSpace.kObject, mfn: om.MFnNurbsSurface = None):
        """
        [UNDOABLE]
        Set the position of all ControlVertices

        Args:
            points (TPointsSequence): the new coordinates of the point
            space (MSpace, optional): the space in which the points are specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        ...

    @property
    def u_cv_count(self):
        mfn = self.apimfn()
        return mfn.numCVsInU

    @property
    def v_cv_count(self):
        mfn = self.apimfn()
        return mfn.numCVsInV

    @property
    def uv_cv_count(self):
        mfn = self.apimfn()
        u = mfn.numCVsInU
        v = mfn.numCVsInV
        return u, v

    @property
    def cv_count(self):
        mfn = self.apimfn()
        u = mfn.numCVsInU
        v = mfn.numCVsInV
        return u * v

    @property
    def u_form(self):
        mfn = self.apimfn()
        return mfn.formInU

    @property
    def v_form(self):
        mfn = self.apimfn()
        return mfn.formInV

    @property
    def is_open_in_u(self):
        if self.u_form == self._mfnClass.kOpen:
            return True

    @property
    def is_open_in_v(self):
        if self.v_form == self._mfnClass.kOpen:
            return True

    @property
    def is_closed_in_u(self):
        if self.u_form == self._mfnClass.kClosed:
            return True

    @property
    def is_closed_in_v(self):
        if self.v_form == self._mfnClass.kClosed:
            return True

    @property
    def is_periodic_in_u(self):
        if self.u_form == self._mfnClass.kPeriodic:
            return True

    @property
    def is_periodic_in_v(self):
        if self.v_form == self._mfnClass.kPeriodic:
            return True

    @property
    def u_knot_count(self):
        mfn = self.apimfn()
        return mfn.numKnotsInU

    @property
    def v_knot_count(self):
        mfn = self.apimfn()
        return mfn.numKnotsInV

    @property
    def u_span_count(self):
        mfn = self.apimfn()
        return mfn.numSpansInU

    @property
    def v_span_count(self):
        mfn = self.apimfn()
        return mfn.numSpansInV

    @property
    def u_knot_domain(self):
        mfn = self.apimfn()
        return mfn.knotDomainInU

    @property
    def v_knot_domain(self):
        mfn = self.apimfn()
        return mfn.knotDomainInV
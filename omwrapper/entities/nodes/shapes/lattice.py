from itertools import product
from typing import Sequence

from maya.api import OpenMaya as om

from omwrapper.constants import ComponentType
from omwrapper.entities.base import recycle_mfn, undoable_proxy_wrap
from omwrapper.entities.factory import ComponentAccessor
from omwrapper.entities.nodes.shapes.base import GeometryShape, TPointsSequence
from omwrapper.pytools import sequence_product


class LatticeShape(GeometryShape):
    _mfn_class = om.MFnDagNode
    _mfn_constant = om.MFn.kLattice

    def _get_mit_id(self, index: Sequence[int]) -> om.MItGeometry:
        """
        Get a geometry iterator for this shape at the given index
        Args:
            index (list, tuple):  the [s, t, u] indices of the Point

        Returns:
            MItGeometry: the OpenMaya iterator for the given component

        """
        mfn = om.MFnTripleIndexedComponent()
        mfn.create(om.MFn.kLatticeComponent)
        mfn.addElement(index)
        it = om.MItGeometry(self.api_dagpath(), mfn.object())
        return it

    def _get_mit(self) -> om.MItGeometry:
        """
        Get a geometry iterator for all the components of this shape
        Args:

        Returns:
            MItGeometry: the OpenMaya iterator for the given component

        """
        mfn = om.MFnTripleIndexedComponent()
        mfn.create(om.MFn.kLatticeComponent)
        mfn.addElements(self._list_indices())
        it = om.MItGeometry(self.api_dagpath(), mfn.object())
        return it


    def get_point(self, index: Sequence[int], space: int = om.MSpace.kObject) -> om.MPoint:
        """
        Query the position of a Lattice Point
        Args:
            index (list, tuple): the [s, t, u] indices of the Point to query
            space (MSpace, optional): the space in which the point is to be returned. Defaults to kObject

        Returns:
            MPoint: the position of the vertex in the required space

        """
        mit = self._get_mit_id(index)
        return mit.position(space=space)

    def set_point_(self, point: om.MPoint, index: Sequence[int], space: int = om.MSpace.kObject):
        """
        [NOT UNDOABLE]
        Set the position of a Point

        Args:
            point (MPoint): the new coordinates of the point
            index (int): the [s,t,u] indices of the Point to query
            space (MSpace, optional): the space in which the point is specified. Defaults to kObject

        Returns:
            None

        """
        mit = self._get_mit_id(index)
        mit.setPosition(point, space=space)

    @undoable_proxy_wrap(get_point, set_point_)
    def set_point(self, point: om.MPoint, index: Sequence[int], space: int = om.MSpace.kObject):
        """
        [UNDOABLE]
        Set the position of a Point

        Args:
            point (MPoint): the new coordinates of the point
            index (int): the [s,t,u] indices of the Point to query
            space (MSpace, optional): the space in which the point is specified. Defaults to kObject

        Returns:
            None

        """
        ...

    def get_points(self, space: int = om.MSpace.kObject) -> om.MPointArray:
        """
        Query the position of all Points
        Args:
            space (MSpace, optional): the space in which the point is to be returned. Defaults to kObject

        Returns:
            MPoint: the position of the vertex in the required space

        """
        mit = self._get_mit()
        return mit.allPositions(space=space)

    @recycle_mfn
    def set_points_(self, points: TPointsSequence, space: int = om.MSpace.kObject):
        """
        [NOT UNDOABLE]
        Set the position of all Points

        Args:
            points (TPointsSequence): the new coordinates of the point
            space (MSpace, optional): the space in which the points are specified. Defaults to kObject

        Returns:
            None

        """
        mit = self._get_mit()
        mit.setAllPositions(points, space=space)

    @recycle_mfn
    @undoable_proxy_wrap(get_points, set_points_)
    def set_points(self, points: TPointsSequence, space: int = om.MSpace.kObject):
        """
        [UNDOABLE]
        Set the position of all Points

        Args:
            points (TPointsSequence): the new coordinates of the point
            space (MSpace, optional): the space in which the points are specified. Defaults to kObject

        Returns:
            None

        """
        ...

    @property
    def x_points_count(self):
        mfn = self.api_mfn()
        plug = mfn.findPlug('sDivisions', False)
        return plug.asInt()

    @property
    def y_points_count(self):
        mfn = self.api_mfn()
        plug = mfn.findPlug('tDivisions', False)
        return plug.asInt()

    @property
    def z_points_count(self):
        mfn = self.api_mfn()
        plug = mfn.findPlug('uDivisions', False)
        return plug.asInt()

    @property
    def xyz_points_count(self):
        mfn = self.api_mfn()
        plug_x = mfn.findPlug('sDivisions', False)
        plug_y = mfn.findPlug('tDivisions', False)
        plug_z = mfn.findPlug('uDivisions', False)
        return plug_x.asInt(), plug_y.asInt(), plug_z.asInt()

    @property
    def points_count(self):
        return sequence_product(self.xyz_points_count)

    def _list_indices(self):
        return list(product(*[range(n) for n in self.xyz_points_count]))

    @property
    def pt(self):
        return ComponentAccessor(dimension=3, length=self.xyz_points_count,
                                 comp_type=ComponentType.LATTICE_POINT, geometry=self.api_dagpath())

from maya.api import OpenMaya as om

from omwrapper.entities.base import recycle_mfn, undoable_proxy_wrap
from omwrapper.entities.nodes.shapes.base import GeometryShape, TPointsSequence


class Mesh(GeometryShape):
    _mfn_class = om.MFnMesh
    _mfn_constant = om.MFn.kMesh

    def api_mfn(self) -> om.MFnMesh:
        return super().api_mfn()

    @classmethod
    def create_(cls, *args, **kwargs) -> None:
        raise NotImplementedError('Mesh.create_ is not implemented yet')

    @classmethod
    def create(cls, *args, **kwargs) -> None:
        raise NotImplementedError('Mesh.create is not implemented yet')

    @recycle_mfn
    def get_point(self, index:int, space:int=om.MSpace.kObject, mfn:om.MFnMesh=None) -> om.MPoint:
        """
        Query the position of a vertex
        Args:
            index (int): the index of the vertex to query
            space (MSpace, optional): the space in which the point is to be returned. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            MPoint: the position of the vertex in the required space

        """
        return mfn.getPoint(index, space=space)

    @recycle_mfn
    def set_point_(self, point:om.MPoint, index: int, space: int = om.MSpace.kObject, mfn: om.MFnMesh = None):
        """
        [NOT UNDOABLE]
        Set the position of a vertex

        Args:
            point (MPoint): the new coordinates of the point
            index (int): the index of the vertex to query
            space (MSpace, optional): the space in which the point is specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        mfn.setPoint(index, point, space=space)

    @recycle_mfn
    @undoable_proxy_wrap(get_point, set_point_)
    def set_point(self, point:om.MPoint, index: int, space: int = om.MSpace.kObject, mfn: om.MFnMesh = None):
        """
        [UNDOABLE]
        Query the position of a vertex

        Args:
            point (MPoint): the new coordinates of the point
            index (int): the index of the vertex to query
            space (MSpace, optional): the space in which the point is specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        ...

    @recycle_mfn
    def get_points(self, space:int=om.MSpace.kObject, mfn:om.MFnMesh=None) -> om.MPointArray:
        """
        Query the position of all the vertices
        Args:
            space (MSpace, optional): the space in which the points are to be returned. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            MPointArray: an array containing the position of the vertices in the required space

        """
        return mfn.getPoints(space=space)

    @recycle_mfn
    def set_points_(self, points: TPointsSequence, space: int = om.MSpace.kObject, mfn: om.MFnMesh = None):
        """
        [NOT UNDOABLE]
        Set the position of all vertices

        Args:
            points (TPointsSequence): the new coordinates of the point
            space (MSpace, optional): the space in which the points are specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None

        """
        mfn.setPoints(points, space=space)

    @recycle_mfn
    @undoable_proxy_wrap(get_points, set_points_)
    def set_points(self, points: TPointsSequence, space: int = om.MSpace.kObject, mfn: om.MFnMesh = None):
        """
        [UNDOABLE]
        Set the position of all vertices

        Args:
            points (TPointsSequence): the new coordinates of the points
            space (MSpace, optional): the space in which the points are specified. Defaults to kObject
            mfn (MFnMesh, optional): the optional function set representing this mesh

        Returns:
            None
        """
        ...

    @property
    def vertex_count(self):
        return self.api_mfn().numVertices

    @property
    def edge_count(self):
        return self.api_mfn().numEdges

    @property
    def face_count(self):
        return self.api_mfn().numPolygons

    @property
    def uv_set_count(self):
        return self.api_mfn().numUVSets
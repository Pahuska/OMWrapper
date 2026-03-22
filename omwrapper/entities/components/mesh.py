from __future__ import annotations

from typing import Union

from maya.api import OpenMaya as om

from omwrapper.entities.components.base import Component1D, ComponentPoint, recycle_mit


class MeshVertex(Component1D, ComponentPoint):
    _mit_class = om.MItMeshVertex
    _mfn_constant = om.MFn.kMeshVertComponent
    _name = '.vtx'

    @recycle_mit
    def connected_edges_count(self, mit:om.MItMeshVertex=None) -> int:
        return mit.numConnectedEdges()

    @recycle_mit
    def connected_faces_count(self, mit: om.MItMeshVertex = None) -> int:
        return mit.numConnectedFaces()

    @recycle_mit
    def connected_edges_count(self, mit: om.MItMeshVertex = None) -> int:
        return len(mit.getConnectedVertices())

    @recycle_mit
    def get_connected_edges(self, mit: om.MItMeshVertex = None) -> "MeshEdge":
        edge_ids = mit.getConnectedEdges()
        if len(edge_ids):
            return self.node().e[edge_ids]

    @recycle_mit
    def get_connected_faces(self, mit: om.MItMeshVertex = None) -> "MeshFace":
        face_ids = mit.getConnectedFaces()
        if len(face_ids):
            return self.node().f[face_ids]

    @recycle_mit
    def get_connected_vertices(self, mit: om.MItMeshVertex = None) -> "MeshVertex":
        vertex_ids = mit.getConnectedVertices()
        if len(vertex_ids):
            return self.node().vtx[vertex_ids]

    @recycle_mit
    def connected_to_face(self, face:Union[int, "MeshFace"], mit: om.MItMeshVertex = None) -> bool:
        if isinstance(face, MeshFace):
            face = face.index()
        return mit.connectedToFace(face)

    @recycle_mit
    def connected_to_edge(self, edge: Union[int, "MeshEdge"], mit: om.MItMeshVertex = None) -> bool:
        if isinstance(edge, MeshEdge):
            edge = edge.index()
        return mit.connectedToEdge(edge)

class MeshFace(Component1D):
    _mit_class = om.MItMeshPolygon
    _mfn_constant = om.MFn.kMeshPolygonComponent
    _name = '.f'

    @recycle_mit
    def vertex_count(self, mit:om.MItMeshPolygon=None) -> int:
        return mit.polygonVertexCount()

    @recycle_mit
    def vertex_index(self, item, mit:om.MItMeshPolygon=None) -> int:
        return mit.vertexIndex(item)

    @recycle_mit
    def get_vertices(self, mit:om.MItMeshPolygon=None) -> MeshVertex:
        vertex_ids = mit.getVertices()
        return self.node().vtx[vertex_ids]

    @recycle_mit
    def get_edges(self, mit:om.MItMeshPolygon=None) -> MeshEdge:
        edge_ids = mit.getEdges()
        return self.node().e[edge_ids]

    @recycle_mit
    def get_area(self, space=om.MSpace.kObject, mit:om.MItMeshPolygon=None) -> float:
        return mit.getArea(space=space)

    @recycle_mit
    def get_connected_faces(self, mit: om.MItMeshPolygon = None) -> "MeshFace":
        face_ids = mit.getConnectedFaces()
        if len(face_ids):
            return self.node().f[face_ids]

    @recycle_mit
    def get_connected_edges(self, mit: om.MItMeshPolygon = None) -> "MeshEdge":
        edge_ids = mit.getConnectedEdges()
        if len(edge_ids):
            return self.node().e[edge_ids]

    @recycle_mit
    def get_connected_vertices(self, mit: om.MItMeshPolygon = None) -> "MeshVertex":
        vertex_ids = mit.getConnectedVertices()
        if len(vertex_ids):
            return self.node().vtx[vertex_ids]

class MeshEdge(Component1D):
    _mit_class = om.MItMeshEdge
    _mfn_constant = om.MFn.kMeshEdgeComponent
    _name = '.e'
from maya.api import OpenMaya as om

from omwrapper.entities.nodes.shapes.base import GeometryShape
from omwrapper.pytools import sequence_product


class LatticeShape(GeometryShape):
    _mfn_class = om.MFnDagNode
    _mfn_constant = om.MFn.kLattice

    @property
    def x_points_count(self):
        mfn = self.apimfn()
        plug = mfn.findPlug('sDivisions', False)
        return plug.asInt()

    @property
    def y_points_count(self):
        mfn = self.apimfn()
        plug = mfn.findPlug('tDivisions', False)
        return plug.asInt()

    @property
    def z_points_count(self):
        mfn = self.apimfn()
        plug = mfn.findPlug('uDivisions', False)
        return plug.asInt()

    @property
    def xyz_points_count(self):
        mfn = self.apimfn()
        plug_x = mfn.findPlug('sDivisions', False)
        plug_y = mfn.findPlug('tDivisions', False)
        plug_z = mfn.findPlug('uDivisions', False)
        return plug_x.asInt(), plug_y.asInt(), plug_z.asInt()

    @property
    def points_count(self):
        return sequence_product(self.numPointsInXYZ)
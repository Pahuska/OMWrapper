from __future__ import annotations

from typing import TYPE_CHECKING, Union

from maya.api import OpenMaya as om

from omwrapper.constants import DataType
from omwrapper.entities.nodes.transform import Transform

if TYPE_CHECKING:
    from omwrapper.entities.attributes.base import Attribute

class Joint(Transform):
    _mfn_constant = om.MFn.kJoint

    def get_joint_orientation(self, as_quat:bool=False) -> Union[om.MEulerRotation, om.MQuaternion]:
        """
        Get the jointOrient component of this joint, in the form of an Euler rotation or a Quaternion
        Args:
            as_quat (bool, optional): True if you want to get a quaternion. False if you want an euler

        Returns:
            (MEulerRotation, MQuaternion): the joint orientation of this joint.

        """
        euler = DataType.to_euler(self.jointOrient.get())
        if as_quat:
            return euler.asQuaternion()
        else:
            return euler

    def zero_rotate(self):
        """
        Zero out the rotate component of this joint, moving values to the jointOrient

        Returns:
            None

        """
        jo = self.jointOrient # type: Attribute
        ro = self.rotate # type: Attribute

        if jo.is_free_to_change() and ro.is_free_to_change():
            j_euler = self.get_joint_orientation()
            r_euler = self.get_rotation()
            euler = r_euler * j_euler # type: om.MEulerRotation
            jo.set([om.MAngle.internalToUI(v) for v in euler.asVector()])
            ro.set([0, 0, 0])

    def zero_joint_orient(self):
        """
        Zero out the jointOrient component of this joint, moving values to the rotate attribute

        Returns:
            None

        """
        jo = self.jointOrient  # type: Attribute
        ro = self.rotate  # type: Attribute

        if jo.is_free_to_change() and ro.is_free_to_change():
            j_euler = self.get_joint_orientation()
            r_euler = self.get_rotation()
            euler = r_euler * j_euler  # type: om.MEulerRotation
            ro.set([om.MAngle.internalToUI(v) for v in euler.asVector()])
            jo.set([0, 0, 0])

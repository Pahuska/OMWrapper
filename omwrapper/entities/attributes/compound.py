from typing import Union
from maya.api import OpenMaya as om
from omwrapper.entities.attributes.base import Attribute
from omwrapper.entities.base import recycle_mfn

TAttrInput = Union[Attribute, om.MObject]

class CompoundAttribute(Attribute):
    """
    Represents a compound attribute that can contain multiple child attributes.
    Provides functionality for manipulating child attributes.
    """

    _mfn_class = om.MFnCompoundAttribute
    _mfn_constant = om.MFn.kCompoundAttribute

    @recycle_mfn
    def child(self, x: int, as_mplug: bool = False, mfn: om.MFnCompoundAttribute = None):
        """
        Retrieve a child attribute by its index.

        Args:
            x (int): The index of the child attribute.
            as_mplug (bool, optional): Whether to return the child as an MPlug. Defaults to False.
            mfn (MFnCompoundAttribute, optional): The function set for the compound attribute.

        Returns:
            Union[MPlug, Attribute]: The child attribute as an MPlug if `as_mplug` is True, otherwise as an Attribute.

        Raises:
            ValueError: If the index is out of range.
        """
        if x >= self.children_count(mfn=mfn):
            raise ValueError('Index out of range')

        obj = mfn.child(x)
        mplug = om.MPlug(obj)
        if as_mplug:
            return mplug

        return self._factory(MPlug=mplug, MObjectHandle=om.MObjectHandle(obj))

    @recycle_mfn
    def add_child(self, attr: TAttrInput, mfn: om.MFnCompoundAttribute = None):
        """
        Add a child attribute to the compound attribute.

        Args:
            attr (TAttrInput): The attribute to add, either as an Attribute instance or an MObject.
            mfn (MFnCompoundAttribute, optional): The function set for the compound attribute.

        Returns:
            None
        """
        if isinstance(attr, Attribute):
            attr = attr.api_mobject()

        mfn.addChild(attr)

    @recycle_mfn
    def remove_child(self, attr: TAttrInput, mfn: om.MFnCompoundAttribute = None):
        """
        Remove a child attribute from the compound attribute.

        Args:
            attr (TAttrInput): The attribute to remove, either as an Attribute instance or an MObject.
            mfn (MFnCompoundAttribute, optional): The function set for the compound attribute.

        Returns:
            None
        """
        if isinstance(attr, Attribute):
            attr = attr.api_mobject()

        mfn.removeChild(attr)

    @recycle_mfn
    def children_count(self, mfn: om.MFnCompoundAttribute = None):
        """
        Get the number of child attributes in the compound attribute.

        Args:
            mfn (MFnCompoundAttribute, optional): The function set for the compound attribute.

        Returns:
            int: The number of child attributes.
        """
        return mfn.numChildren()
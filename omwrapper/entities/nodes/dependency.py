from typing import Dict

from maya.api import OpenMaya as om

from omwrapper.api.modifiers.base import TModifier, add_modifier
from omwrapper.api.modifiers.custom import ProxyModifier
from omwrapper.api.modifiers.maya import DGModifier
from omwrapper.api.utilities import name_to_api
from omwrapper.entities.attributes.base import AttributeHandler, AttrData, AttrFactory
from omwrapper.entities.base import MayaObject, TMayaObjectApi, recycle_mfn
from omwrapper.api import apiundo


class DependNode(MayaObject):
    _mfn_class = om.MFnDependencyNode
    _mfn_constant = om.MFn.kDependencyNode

    def __init__(self, **kwargs: TMayaObjectApi):
        super().__init__(**kwargs)
        self._attribute_handler = AttributeHandler(self.api_mobject())

    def api_mfn(self) -> om.MFnDependencyNode:
        return self._mfn_class(self.api_mobject())

    def name(self, full_dag_path:bool=False) -> str:
        mfn = om.MFnDependencyNode(self.api_mobject())
        return mfn.name()

    @classmethod
    def get_build_data_from_name(cls, name:str) -> Dict[str, TMayaObjectApi]:
        mobj = name_to_api(name)
        if not isinstance(mobj, om.MObject):
            raise TypeError(f'{name} is not a Dependency Node')

        return {'MObjectHandle': om.MObjectHandle(mobj)}

    @recycle_mfn
    def rename_(self, name:str, mfn:om.MFnDependencyNode) -> str:
        """
        Rename the node - NOT UNDOABLE -

        Args:
            name (str): the new name of the node
            mfn (MFnDependencyNode, optional): an optional compatible MFn.

        Returns:
            str: the new name of the node

        """
        name = mfn.setName(name)
        return name

    @add_modifier(DGModifier, undo=True)
    def rename(self, name:str, _modifier:TModifier) -> str:
        """
        Rename the node

        Args:
            name (str): the new name of the node
            _modifier (AbstractModifier, MDGModifier, MDagModifier, optional): an optional modifier object. if one is
                provided, it will be up to the user to execute the doIt function and handle the undo behavior

        Returns:
            str: the new name of the node

        """
        _modifier.renameNode(self.api_mobject(), name)
        return self.name()

    def has_attr(self, name:str) -> bool:
        """
        Verify whether an attribute with the given name exists on this node

        Args:
            name (str): the name of the attribute

        Returns:
            bool: True if it exists, False otherwise

        """
        mfn = om.MFnDependencyNode(self.api_mobject())
        return mfn.hasAttribute(name)

    def add_attr(self, data:AttrData, _modifier:DGModifier=None):
        fn = AttrFactory(data)
        self._attribute_handler.add_attribute(fn=fn, children_count=data.children_count,
                                              parent=data.parent, _modifier=_modifier)

    def attr_handler(self) -> AttributeHandler:
        return self._attribute_handler

    @recycle_mfn
    def is_locked(self, mfn:om.MFnDependencyNode) -> bool:
        """
        Whether this node is locked or not

        Returns:
            bool: True if the node is locked, False otherwise
            mfn (MFnDependencyNode, optional): an optional compatible MFn.

        """
        locked = mfn.isLocked
        return locked

    @recycle_mfn
    def set_locked_(self, value:bool, mfn:om.MFnDependencyNode):
        mfn.isLocked = value

    @recycle_mfn
    def set_locked(self, value:bool, mfn:om.MFnDependencyNode):
        old_value = mfn.isLocked
        modifier = ProxyModifier(do_func=self.set_locked_, do_kwargs={'value':value, 'mfn':mfn},
                                 undo_kwargs={'value':old_value, 'mfn':mfn})
        modifier.doIt()

        apiundo.commit(undo=modifier.undoIt, redo=modifier.doIt)

        return modifier
from typing import Dict, Union

from maya.api import OpenMaya as om

from omwrapper.api import apiundo
from omwrapper.api.modifiers.maya import DagModifier
from omwrapper.api.utilities import name_to_api
from omwrapper.entities.base import TMayaObjectApi, recycle_mfn
from omwrapper.entities.nodes.dependency import DependNode


class DagNode(DependNode):
    _mfn_class = om.MFnDagNode
    _mfn_constant = om.MFn.kDagNode

    def api_dagpath(self):
        return self._api_input['MDagPath']

    def api_mfn(self) -> om.MFnDagNode:
        self._mfn_class(self.api_dagpath())

    @classmethod
    def get_build_data_from_name(cls, name:str) -> Dict[str, TMayaObjectApi]:
        mobj = name_to_api(name)
        if not isinstance(mobj, om.MObject):
            raise TypeError(f'{name} is not a Dependency Node')

        return {'MObjectHandle': om.MObjectHandle(mobj)}

    def name(self, full_dag_path:bool=False) -> str:
        mfn = om.MFnDagNode(self.api_mobject())
        if full_dag_path:
            return mfn.fullPathName()
        return mfn.name()

    def get_parent(self, index:int=1):
        if index == 0:
            return self

        mobj = self.api_mobject()
        for x in range(index):
            mobj = om.MFnDagNode(mobj).parent(0)
            if mobj.apiType() == om.MFn.kWorld:
                return None
        return self._factory(MObject=mobj)

    @recycle_mfn
    def get_children(self, mfn:om.MFnDagNode) -> "DagNode":
        for x in range(mfn.childCount()):
            yield self._factory(MObject=mfn.child(x))

    def _get_selectable_object(self) -> om.MDagPath:
        return self.api_dagpath()

    @classmethod
    def _create(cls, node_type: Union[str, int], name: str = None,
                parent:Union[om.MObject, "DagNode"]=None) -> "DagNode":
        """
        NOT UNDOABLE
        Create a new Dependency node of the given type. If no name is specified, it will be based on the node_type
        Args:
            node_type (str, MFn.TypeId): either a string of an MFn.TypeId constant representing the desired node type
            name (str, optional): the name of the newly created node
            parent (MObject, DagNode, optional): The optional parent of the node. Defaults to None

        Returns:
            DependNode: the created node
        """
        mfn = cls._mfn_class()
        if parent is None:
            parent = om.MObject.kNullObj
        elif isinstance(parent, DagNode):
            parent = parent.api_mobject()

        obj = mfn.create(node_type, name, parent=parent)
        return cls._factory(MObject=obj)

    @classmethod
    def create(cls, node_type: Union[str, int], name: str = None, parent:Union[om.MObject, "DagNode"]=None) -> "DagNode":
        """
        UNDOABLE
        Create a new Dependency node of the given type. If no name is specified, it will be based on the node_type
        Args:
            node_type (str, MFn.TypeId): either a string of an MFn.TypeId constant representing the desired node type
            name (str, optional): the name of the newly created node
            parent (MObject, DagNode, optional): The optional parent of the node. Defaults to None

        Returns:
            DependNode: the created node
        """

        if parent is None:
            parent = om.MObject.kNullObj
        elif isinstance(parent, DagNode):
            parent = parent.api_mobject()

        mod = DagModifier()
        obj = mod.create_node(node_type=node_type, name=name, parent=parent)
        mod.doIt()
        apiundo.commit(undo=mod.undoIt, redo=mod.doIt)
        return cls._factory(MObject=obj)
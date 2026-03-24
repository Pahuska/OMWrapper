from __future__ import annotations
from typing import Dict, Union

from maya.api import OpenMaya as om

from omwrapper.api import apiundo
from omwrapper.api.modifiers.custom import ProxyModifier
from omwrapper.api.modifiers.maya import DagModifier
from omwrapper.api.utilities import name_to_api
from omwrapper.entities.base import TMayaObjectApi, recycle_mfn
from omwrapper.entities.nodes.dependency import DependNode

#ToDo: addChild and setParent
class DagNode(DependNode):
    _mfn_class = om.MFnDagNode
    _mfn_constant = om.MFn.kDagNode

    def api_dagpath(self):
        return self._api_input['MDagPath']

    def api_mfn(self) -> om.MFnDagNode:
        return self._mfn_class(self.api_dagpath())

    @classmethod
    def get_build_data_from_name(cls, name:str) -> Dict[str, TMayaObjectApi]:
        dag = name_to_api(name)
        if not isinstance(dag, om.MDagPath):
            raise TypeError(f'{name} is not a DAG Node')

        return {'MDagPath': dag, 'MObjectHandle': om.MObjectHandle(dag.node())}

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
    def get_children(self, mfn:om.MFnDagNode=None) -> "DagNode":
        for x in range(mfn.childCount()):
            yield self._factory(MObject=mfn.child(x))

    @recycle_mfn
    def get_child(self, index:int, mfn:om.MFnDagNode=None):
        return self._factory(MObject=mfn.child(index))

    def _get_selectable_object(self) -> om.MDagPath:
        return self.api_dagpath()

    @classmethod
    def create_(cls, node_type: Union[str, int], name: str = None,
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

    @recycle_mfn
    def add_child_(self, node:Union["DagNode", om.MObject, om.MObjectHandle], index:int=None, keep_parent:bool=False, mfn:om.MFnDagNode=None):
        """
        [NOT UNDOABLE]
        Insert the given node in the hierarchy of the current node at the given index.

        Parameters:
            node (DagNode, MObject, MObjectHandle): the node to add in the current node hierarchy
            index (int, Optional): the position of the node in the hierarchy
            keep_parent (Bool, Optional): if True, the node will be removed from its current parent(s). Defaults to True
            mfn (MFnAttribute, optional): The attribute function set (`MFnAttribute`) to retrieve the name from.
                If not provided, the decorator or other logic may handle the setup. Defaults to None.

        Returns:
            None
        """
        if not isinstance(node, om.MObject):
            node = node.api_mobject()
        elif isinstance(node, om.MObjectHandle):
            node = node.object()

        if index is None:
            index = mfn.kNextPos
        mfn.addChild(node, index, keep_parent)

    @recycle_mfn
    def remove_child_(self, node:Union["DagNode", om.MObject, om.MObjectHandle], mfn:om.MFnDagNode=None):
        """
        [NOT UNDOABLE]
        remove the given node from the hierarchy of the current node.

        Parameters:
            node (DagNode, MObject, MObjectHandle): the node to remove in the current node hierarchy
            mfn (MFnAttribute, optional): The attribute function set (`MFnAttribute`) to retrieve the name from.
                If not provided, the decorator or other logic may handle the setup. Defaults to None.

        Returns:
            None
        """

        if not isinstance(node, om.MObject):
            node = node.api_mobject()
        elif isinstance(node, om.MObjectHandle):
            node = node.object()

        mfn.removeChild(node)

    @recycle_mfn
    def remove_child_at_(self, index:int, mfn: om.MFnDagNode = None):
        """
        [NOT UNDOABLE]
        remove the node at the given index from the hierarchy of the current node.

        Parameters:
            index (int): the index of the child to be removed
            mfn (MFnAttribute, optional): The attribute function set (`MFnAttribute`) to retrieve the name from.
                If not provided, the decorator or other logic may handle the setup. Defaults to None.

        Returns:
            None
        """
        mfn.removeChildAt(index)

    @recycle_mfn
    def add_child(self, node: Union["DagNode", om.MObject, om.MObjectHandle], index: int = None, keep_parent: bool = False,
                   mfn: om.MFnDagNode = None):
        """
        [UNDOABLE]
        Insert the given node in the hierarchy of the current node at the given index.

        Parameters:
            node (DagNode, MObject, MObjectHandle): the node to add in the current node hierarchy
            index (int, Optional): the position of the node in the hierarchy
            keep_parent (Bool, Optional): if True, the node will be removed from its current parent(s). Defaults to True
            mfn (MFnAttribute, optional): The attribute function set (`MFnAttribute`) to retrieve the name from.
                If not provided, the decorator or other logic may handle the setup. Defaults to None.

        Returns:
            None
        """
        if not isinstance(node, om.MObject):
            node = node.api_mobject()
        elif isinstance(node, om.MObjectHandle):
            node = node.object()

        parents = []
        ids = []

        # If keep_parent is false, then we need to restore them in the undoing function, so we're building a list of all
        #  the parents and another of the indices of the child in each parent
        if not keep_parent:
            child_fn = om.MFnDagNode(node)
            parents = [child_fn.parent(x) for x in range(child_fn.parentCount())]
            for parent in parents:
                fn = om.MFnDagNode(parent)
                for x in range(fn.childCount()):
                    if fn.child(x) == node:
                        ids.append(x)
                        break

        def undo_func():
            mfn.removeChild(node)
            if not keep_parent:
                for p, idx in zip(parents, ids):
                    f = om.MFnDagNode(p)
                    f.addChild(node, index=idx, keepExistingParents=True)

        do_kwargs = {'node':node, 'index':index, 'keep_parent':keep_parent, 'mfn':mfn}
        mod = ProxyModifier(do_func=self.add_child_, do_kwargs=do_kwargs, undo_func=undo_func)
        mod.doIt()
        apiundo.commit(undo=mod.undoIt, redo=mod.doIt)


    @recycle_mfn
    def remove_child(self, node: Union["DagNode", om.MObject, om.MObjectHandle], mfn: om.MFnDagNode = None):
        """
        [UNDOABLE]
        remove the given node from the hierarchy of the current node.

        Parameters:
            node (DagNode, MObject, MObjectHandle): the node to remove in the current node hierarchy
            mfn (MFnAttribute, optional): The attribute function set (`MFnAttribute`) to retrieve the name from.
                If not provided, the decorator or other logic may handle the setup. Defaults to None.

        Returns:
            None
        """
        if not isinstance(node, om.MObject):
            node = node.api_mobject()
        elif isinstance(node, om.MObjectHandle):
            node = node.object()

        index = None
        for x in range(mfn.childCount()):
            if mfn.child(x) == node:
                index = x
                break

        do_kwargs = {'node': node, 'mfn': mfn}
        undo_kwargs = {'node': node, 'index': index, 'keep_parent': True, 'mfn': mfn}
        mod = ProxyModifier(do_func=self.remove_child_, do_kwargs=do_kwargs,
                            undo_func=self.add_child_, undo_kwargs=undo_kwargs)
        mod.doIt()
        apiundo.commit(undo=mod.undoIt, redo=mod.doIt)

    @recycle_mfn
    def remove_child_at(self, index: int, mfn: om.MFnDagNode = None):
        """
        [UNDOABLE]
        remove the node at the given index from the hierarchy of the current node.

        Parameters:
            index (int): the index of the child to be removed
            mfn (MFnAttribute, optional): The attribute function set (`MFnAttribute`) to retrieve the name from.
                If not provided, the decorator or other logic may handle the setup. Defaults to None.

        Returns:
            None
        """
        node = mfn.child(index)

        do_kwargs = {'index': index, 'mfn': mfn}
        undo_kwargs = {'node': node, 'index': index, 'keep_parent': True, 'mfn': mfn}
        mod = ProxyModifier(do_func=self.remove_child_at_, do_kwargs=do_kwargs,
                            undo_func=self.add_child_, undo_kwargs=undo_kwargs)
        mod.doIt()
        apiundo.commit(undo=mod.undoIt, redo=mod.doIt)
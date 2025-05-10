from typing import Union, List

from maya import cmds
from maya.api import OpenMaya as om

from omwrapper.api.modifiers.maya import DagModifier, DGModifier
from omwrapper.api.utilities import name_to_api
from omwrapper.entities.base import MayaObject
from omwrapper.entities.factory import PyObject
from omwrapper.entities.registration import pyobject
from omwrapper.api import apiundo

factory = PyObject()

def create_node(node_type:str, name:str=None, parent:Union[MayaObject, str, om.MObject]=None,
                _modifier:Union[DagModifier, DGModifier]=None, _is_dag:bool=None) -> MayaObject:
    """
    Create a new node of the given type.

    The user can choose to pass your own DGModifier or DagModifier to create the node. in that case, the doIt() method
    won't be called and the modifier won't be commited to the undo queue. Also, if a modifier is provided by the user,
    there won't be a check to verify that its type matches the provided node_type (i.e. a Transform node requires a
    DagModifier, while a MultiplyDivide requires a DGModifier).

    Args:
        node_type (str): the type of the node
        name (str, optional): the name of the node. If none is provided, a default name will be used, based on the node
         type
        parent (MayaObject, str, MObject, optional): In the case of a DAG node, the optional parent of the node. If none
         is provided, the new node will be parented to the world or under a new transform, and this transform will be
          returned instead
        _modifier (DagModifier, DGModifier, optional): the optional modifier to be used to create the node. Defaults to
         DagModifier or DGModifier depending on the required node type
        _is_dag (bool, optional): an optional flag to tell if the node is a Dag or DG, thus skipping the checking step

    Returns:
        MayaObject: the new node

    """
    kwargs = {'name':name}
    if _modifier is None:
        do_it = True
        if _is_dag is None:
            if  'dagNode' in cmds.nodeType(node_type, inherited=True, isTypeName=True):
                mod = DagModifier()
                _is_dag = True
            else:
                mod = DGModifier()
                _is_dag = False
        elif _is_dag:
            mod = DagModifier()
        else:
            mod = DGModifier()
    else:
        mod = _modifier
        do_it = False

    if parent is not None:
        if isinstance(parent, MayaObject):
            parent = parent.api_mobject()
        elif isinstance(parent, str):
            parent = name_to_api(parent, as_mobject=True)
        kwargs['parent'] = parent

    obj = mod.create_node(node_type=node_type, **kwargs)
    if do_it:
        mod.doIt()
        apiundo.commit(undo=mod.undoIt, redo=mod.doIt)
    return factory(MObject=obj)

def selected() -> List[MayaObject]:
    """
    Get the selected objects

    Returns:
        list: the selected objects

    """
    return factory.from_selection_list(om.MGlobal.getActiveSelectionList())


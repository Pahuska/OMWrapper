from __future__ import annotations

import inspect
from abc import abstractmethod
from functools import wraps
from typing import Tuple, TYPE_CHECKING, Union, Iterable, Callable

from maya.api import OpenMaya as om

from omwrapper.api.modifiers.base import add_modifier
from omwrapper.api.modifiers.maya import DagModifier
from omwrapper.constants import DataType
from omwrapper.entities.base import MayaObject, TMayaObjectApi, recycle_mfn, undoable_proxy_wrap
from omwrapper.pytools import Iterator

if TYPE_CHECKING:
    from omwrapper.entities.nodes.shapes.base import GeometryShape

def recycle_mit(func:Callable):
    @wraps(func)
    def wrapped(*args, **kwargs):
        signature = inspect.signature(func)
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        bound_kwargs = bound_args.arguments

        inst = bound_kwargs['self']
        mfn = bound_kwargs.get('mit', None)
        if mfn is None:
            bound_kwargs['mit'] = inst.api_mit()
        result = func(**bound_kwargs)
        return result
    return wrapped

class Component(MayaObject):
    _mfn_class = om.MFnComponent
    _mfn_constant = None
    _mit_class = om.MItGeometry
    _name = '.component'
    _id_count = 1

    def __init__(self, **kwargs:TMayaObjectApi):
        self._node = kwargs.pop('node', None)
        super().__init__(**kwargs)

    def __len__(self):
        return self.api_mfn().elementCount

    def api_dagpath(self) -> om.MDagPath:
        return self._api_input['MDagPath']

    def api_mfn(self) -> om.MFnComponent:
        return self._mfn_class(self.api_mobject())

    def api_mit(self) -> om.MItGeometry:
        return self._mit_class(self.api_dagpath(), self.api_mobject())

    @abstractmethod
    def _extract_element(self, item:int) -> Union[om.MIntArray, list]:
        """
        Extract a single item from the MFnComponent at the given index

        Args:
            item (int): the index of the component

        Returns:
            MIntArray : the extracted component in an array
        """
        ...

    def api_mit_id(self, item:int):
        ...

    #ToDo: figure out a way to return a name usable in cmds
    def name(self, full_dag_path:bool=False) -> str:
        fdp = self.api_dagpath().fullPathName()
        if len(self) == 1:
            elem = self._extract_element(0)[0]
            if not isinstance(elem, (tuple, list)):
                comp_name = self._name + ''.join('[{}]'.format(elem))
            else:
                comp_name = self._name + ''.join('[{}]'.format(x) for x in elem)
        else:
            comp_name = self._name + 'Array'
        if full_dag_path:
            path = fdp
        else:
            path = fdp.split('|')[-1]
        return path + comp_name

    def node(self) -> "GeometryShape":
        if self._node is None:
            dag = self.api_dagpath()
            self._node = self._factory(MDagPath=dag, MObjectHandle=om.MObjectHandle(dag.node()))
        return self._node

    @classmethod
    def get_build_data_from_name(cls, name):
        sel = om.MSelectionList()
        sel.add(name)

        try:
            comp = sel.getComponent(0)
        except TypeError:
            raise TypeError('{} is not a valid component'.format(name))

        if comp[1] == om.MObject.kNullObj:
            raise TypeError('{} is empty'.format(name))

        return {'MObjectHandle': om.MObjectHandle(comp[1]), 'MDagPath': comp[0]}

    def _get_selectable_object(self) -> Tuple[om.MDagPath, om.MObject]:
        return self.api_dagpath(), self.api_mobject()

    def index(self, item=0) -> int:
        return self._extract_element(item)[0]

    def indices(self):
        return self.api_mfn().getElements()

class ComponentPoint(Component):

    def get_position(self, item:int, space=om.MSpace.kObject) -> om.MPoint:
        point_id = self._extract_element(item)[0]
        return self.node().get_point(index=point_id, space=space)

    def set_position_(self, value:Union[om.MPoint, om.MVector, Iterable], item:int, space=om.MSpace.kObject,
                      relative:bool=False):
        self._pre_set_position(value=value, item=item, space=space, relative=relative)
        if relative:
            vector = DataType.to_vector(value)
            point = self.get_position(item=item, space=space) + vector
        else:
            point = DataType.to_point(value)

        point_id = self._extract_element(item)[0]
        self.node().set_point_(point=point, index=point_id, space=space)

        self._post_set_position(value=value, item=item, space=space, relative=relative)

    @undoable_proxy_wrap(get_position, set_position_, {'relative':False})
    def set_position(self):
        ...

    def get_positions(self, space=om.MSpace.kObject) -> om.MPointArray:
        it = self.api_mit()
        result = om.MPointArray()
        while not it.isDone():
            result.append(it.position(space=space))
            it.next()
        return result

    def set_positions_(self, points, space=om.MSpace.kObject, relative=False):
        self._pre_set_positions(points=points, space=space, relative=relative)
        it = self.api_mit()
        if it.count() != len(points):
            raise ValueError('The points array length does not match the vertex count')
        point_it = Iterator(points)
        while not it.isDone():
            if relative:
                p = it.position(sapce=space) + DataType.to_vector(point_it.current_item())
            else:
                p = DataType.to_point(point_it.current_item())
            it.setPosition(p, space=space)
            it.next()
            point_it.next()
        self._post_set_positions(points=points, space=space, relative=relative, mit=it)

    @undoable_proxy_wrap(get_positions, set_positions_, {'relative': False})
    def set_positions(self):
        ...

    def _pre_set_position(self, *args, **kwargs):
        ...

    def _post_set_position(self, *args, **kwargs):
        ...

    def _pre_set_positions(self, *args, **kwargs):
        ...

    def _post_set_positions(self, *args, **kwargs):
        ...

    def get_bounding_box(self, space=om.MSpace.kObject):
        bbox = om.MBoundingBox()
        it = self.api_mit()
        while not it.isDone():
            bbox.expand(it.position(space=space))
            it.next()
        return bbox

class Component1D(Component):
    _mfn_class = om.MFnSingleIndexedComponent
    _id_count = 1

    def api_mfn(self) -> om.MFnSingleIndexedComponent:
        return super().api_mfn()

    def _extract_element(self, item:int) -> om.MIntArray:
        elem = self.api_mfn().element(item)
        return om.MIntArray([elem])

class Component2D(Component):
    _mfn_class = om.MFnDoubleIndexedComponent
    _id_count = 2

    def api_mfn(self) -> om.MFnDoubleIndexedComponent:
        return super().api_mfn()

    def _extract_element(self, item:int) -> list:
        elem = self.api_mfn().getElement(item)
        return [elem]

class Component3D(Component):
    _mfn_class = om.MFnTripleIndexedComponent
    _id_count = 3

    def api_mfn(self) -> om.MFnTripleIndexedComponent:
        return super().api_mfn()

    def _extract_element(self, item:int) -> list:
        elem = self.api_mfn().getElement(item)
        return [elem]

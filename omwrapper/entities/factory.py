from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import product
from typing import overload, Tuple, Union, Callable, Any, TYPE_CHECKING, List
import inspect

from maya.api import OpenMaya as om

from omwrapper.api.utilities import name_to_api, prod_list
from omwrapper.constants import ObjectType, AttributeType, ComponentType, AttrType, DataType

if TYPE_CHECKING:
    from enum import Enum
    from omwrapper.entities.attributes.base import AttrData

class PyObject:
    """
    Singleton Factory class responsible for creating the right subclass of MayaObject
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
        return cls._instance

    def __call__(self, *args, **kwargs) -> Any:
        return self._create(*args, **kwargs)

    def register(self, object_type:Enum, cls:Callable):
        self._registry[object_type] = cls

    @overload
    def _create(self, args: str) -> Any:
        """
        Create a new MayaObject instance from an object name
        Args:
            args (str): a string representing the object name
        Returns:
            MayaObject: a MayaObject instance representing the given object
        """
        ...

    @overload
    def _create(self, args: Tuple[om.MDagPath, Union[om.MObject, om.MObjectHandle]]) -> Any:
        """
        Create a new MayaObject instance from a combination of MDagPath and MObject. Used for Components
        Args:
            args (tuple): a tuple with a MDagPath and a MObject or MObjectHandle
        Returns:
            MayaObject: a MayaObject instance representing the given object
        """
        ...

    @overload
    def _create(self, *args: Union[om.MDagPath, om.MObjectHandle, om.MObject, om.MPlug]) -> Any:
        """
        Create a new MayaObject instance from various API objects. This method is just here for convenience, allowing
        the user to use it with non-keyword arguments. Eventually all the arguments passed will be identified and the
        PyObject will be called again with keyword arguments.
        Args:
            *args (MDagPath | MObject | MObjectHandle | MPlug): one or more API objects
        Returns:
            MayaObject: a MayaObject instance representing the given object
        """
        ...

    @overload
    def _create(self, MPlug: om.MPlug = None,
                MObjectHandle: om.MObjectHandle = None,
                MObject: om.MObject = None,
                MDagPath: om.MDagPath = None,
                ) -> Any:
        """
        Create a new MayaObject instance from various API objects. Different objects are needed depending on the type of
        the object.
        Args:
            MPlug (MPlug): an MPlug Instance representing an attribute
            MObjectHandle (MObjectHandle): an MObjectHandle instance representing a maya object
            MObject (MObject): an MObject instance representing a maya object. If the object is a dag node and no
            MDagPath is provided, then it will look for the first instance of this node
            MDagPath (MDagPath): an MDagPath  instance representing a dag node
        Returns:
            MayaObject: a MayaObject instance representing the given object
        """
        ...

    def _create(self, *args, **kwargs) -> Any:
        """
        Create a new MayaObject from various type of inputs. Check the overloaded methods for more details
        Returns:
             MayaObject: a MayaObject instance representing the given object
        """
        assert len(args) <= 1, 'PyObject does not take more than 1 non-keyword parameter'

        #ToDo : make a method somewhere that would convert args into kwargs so that we can use that to jump straight to
        # case 4 and avoid the situation where we get a string, process it, pass it back into PyObject, process it again
        # and pass it a third time into PyObject (although is it really that bad ? ask Copilot maybe ?)
        if len(args) == 1:
            # CASE 1 : a string was provided, and we are looking for a corresponding API object. We then call PyObject
            # again with whatever we found
            arg = args[0]
            if isinstance(arg, str):
                return self._create(name_to_api(arg), **kwargs)
            else:
                dic = {}
                if isinstance(arg, tuple):
                    # CASE 2 : a tuple was provided, and it contains an MDagPath and an MObject or MObjectHandle
                    # we put them in a dict and pass it as kwargs back into PyObject
                    assert len(arg) == 2, 'PyObjectFactory : Invalid tuple length'
                    assert isinstance(arg[0], om.MDagPath) and isinstance(arg[1], (om.MObject, om.MObjectHandle)), \
                        'PyObject : Invalid tuple composition'

                    for obj in arg:
                        dic[obj.__class__.__name__] = obj
                else:
                    # CASE 3 : one or more API object were provided, such as MPlug, MDagPath, MObject...
                    # we identify them and pass them back as kwargs into PyObject
                    assert isinstance(arg, (om.MDagPath, om.MObjectHandle, om.MObject, om.MPlug)), \
                        f'PyObject : Invalid param type {type(arg)}'

                    dic[arg.__class__.__name__] = arg
                dic.update(kwargs)
                return self._create(**dic)
        else:
            # CASE 4 : keywords args for any of the supported Maya API objects were provided, and we are going to treat
            # them in a specific order to get the right MayaObject out of it. Eventually, all the previous cases end up
            # being treated here.
            assert any(k in ('MDagPath', 'MObject', 'MObjectHandle', 'MPlug') for k in kwargs), \
                'PyObject keyword parameter needs at least one of : (MDagPath, MObject, MObjectHandle, MPlug)'

            if 'MPlug' in kwargs:
                # CASE 4A : an MPlug was provided. Let's get an MObject out of it
                mobj = kwargs['MPlug'].attribute()
            elif 'MObjectHandle' in kwargs:
                # CASE 4B : an MObjectHandle was provided. Let's get an MObject out of it
                mobj = kwargs['MObjectHandle'].object()
            else:
                # CASE 4C : none of the above were provided, assume an MDagPath was
                mobj = kwargs.pop('MObject', None)
                if mobj is None:
                    mobj = kwargs['MDagPath'].node()
                # else:
                #     raise ValueError(f'Not enough data to build a PyObject : {kwargs}')

            # If the MObject is a DagNode but no DagNode was provided, get one
            if 'MDagPath' not in kwargs and mobj.hasFn(om.MFn.kDagNode):
                kwargs['MDagPath'] = om.MDagPath.getAPathTo(mobj)

            # If no MObjectHandle was provided, make one
            if 'MObjectHandle' not in kwargs:
                kwargs['MObjectHandle'] = om.MObjectHandle(mobj)

            for mfn in ObjectType.iter_mfn():
                if mobj.hasFn(mfn):
                    object_type = ObjectType.from_mfn(mfn)
                    break
            else:
                raise TypeError(f'Unrecognized api type : {mobj.apiType}')

            selector = self._registry.get(object_type)
            if selector is None:
                raise NotImplementedError(f'{object_type} is not yet implemented')
            _class = selector(**kwargs)

            try:
                _class = user_class_manager.get_user_class(_class, mobj)
            except ValueError:
                ...
            #ToDo: test this ^

            return _class(**kwargs)

    def from_selection_list(self, sel:om.MSelectionList):
        it = om.MItSelectionList(sel)

        while not it.isDone():
            item_type = it.itemType()
            if item_type == it.kDNselectionItem:
                mobj = it.getDependNode()
                yield self._create(MObjectHandle=om.MObjectHandle(mobj))
            elif item_type == it.kDagSelectionItem:
                if it.hasComponents():
                    mdag, mobj = it.getComponent()
                    yield self._create(MDagPath=mdag, MObjectHandle=om.MObjectHandle(mobj))
                else:
                    mdag = it.getDagPath()
                    yield self._create(MDagPath=mdag, MObjectHandle=om.MObjectHandle(mdag.node()))
            elif item_type == it.kPlugSelectionItem:
                mplug = it.getPlug()
                yield  self._create(MPlug=mplug)
            else:
                raise TypeError(f'Unable to find a matching constructor for {it.getStrings()}')
            it.next()

class ComponentAccessor:
    def __init__(self, dimension:int, length:Union[int, list, tuple], comp_type:ComponentType, geometry:om.MDagPath):
        self.dimension = dimension
        if not isinstance(length, (tuple, list)):
            self.length = [length]
        else:
            self.length = length

        assert len(self.length) == self.dimension, 'Length parameter must match the dimension'
        self.id_array = []
        self.comp_type = comp_type
        self.geometry = geometry

    def __len__(self):
        return self.length

    def __getitem__(self, item):
        # Make sure we haven't already reached the maximum dimension (shouldn't happen anyway)
        assert len(self.id_array) <= self.dimension, f'Cannot slice more than {self.dimension} times'

        array = om.MIntArray()
        if not isinstance(item, (tuple, list, om.MIntArray)):
            item = [item]

        current_dim = len(self.id_array)
        for i in item:
            if isinstance(i, int):
                array.append(i)
            elif isinstance(i, slice):
                start = i.start
                stop = i.stop
                step = i.step

                if start is None:
                    start = 0
                if stop is None:
                    stop = self.length[current_dim] - 1
                if step  is None:
                    step = 1

                if step > 0:
                    stop += 1
                else:
                    stop -= 1

                for x in range(start, stop, step):
                    array.append(x)
        self.id_array.append(array)

        # Keep returning itself until we've processed all dimensions, only then can we build the component
        if len(self.id_array) == self.dimension:
            return self.build()
        else:
            return self

    def is_valid(self):
        return len(self.id_array) == self.dimension

    def compute_elements(self):
        if self.dimension == 1:
            return self.id_array[0]
        else:
            return list(product(*self.id_array))

    def build(self):
        elements = self.compute_elements()
        mfn = self._get_comp_class()(self.geometry.node())
        mfn.create(ComponentType.to_mfn(self.comp_type))
        mfn.addElements(elements)
        factory = PyObject()
        component = factory(MDagPath=self.geometry, MObjectHandle=om.MObjectHandle(mfn.object()))
        return component

    def _get_comp_class(self):
        if self.dimension == 1:
            return om.MFnSingleIndexedComponent
        elif self.dimension == 2:
            return om.MFnDoubleIndexedComponent
        elif self.dimension == 3:
            return om.MFnTripleIndexedComponent

class BaseSelector(ABC):
    def __init__(self, object_type:ObjectType):
        self.object_type = object_type
        self._registry = {}

    def __call__(self, *args, **kwargs):
        return self.get_class(*args, **kwargs)

    def register(self, sub_type:Enum, cls:Callable):
        self._registry[sub_type] = cls

    def get_class(self, MObjectHandle:om.MObjectHandle, **kwargs) -> Callable:
        obj = MObjectHandle.object()

        sub_type_enum = ObjectType.get_subtype(self.object_type)
        for sub_mfn in sub_type_enum.iter_mfn():
            if obj.hasFn(sub_mfn):
                exact_type = sub_type_enum.from_mfn(sub_mfn)
                break
        else:
            exact_type = self.object_type

        cls = self._registry.get(exact_type)
        if cls is None:
            raise NotImplementedError(f'{exact_type} is not yet implemented')
        return cls

class AttributeSelector(BaseSelector):
    MULTI = 'Multi'
    def get_class(self, MPlug:om.MPlug, **kwargs) -> Callable:
        if MPlug.isArray:
            return self._registry.get(self.MULTI)
        else:
            return super().get_class(**kwargs)

class AttrFactory:
    def __new__(cls, data:AttrData) -> om.MFnAttribute:
        """
        Factory class responsible for creating the appropriate function set (MFnAttribute and subclasses) from the data
        that were provided.

        We first find the right function set.
        The next step is to call the create function to actually create the attribute. Different types of attribute will
        have different way to call the create function.
        Finally, we do some post-processing, like adding fields to ENUM attributes, setting the min and max, etc...

        Args:
            data (AttrData): the data to build the MFn from

        Returns:
            MFnAttribute: the new MFnAttribute instance, created and ready to be added to a node
        """

        # CREATE
        # Get the proper function set depending on the AttrType
        mfn = AttrType.to_function_set(data.attr_type)()

        # Call the create appropriate function. Special cases like COLOR and FLOAT3 have a different create function
        if data.attr_type == AttrType.NUMERIC and data.data_type in (DataType.COLOR, DataType.FLOAT3):
            if data.data_type == DataType.COLOR:
                mfn.createColor(*data.create_args)
            elif data.data_type == DataType.FLOAT3:
                mfn.createPoint(*data.create_args)
        else:
            mfn.create(*data.create_args)

        # POST PROCESS
        # For the ENUM type we must add the fields one by one
        # Then we set the default value, which can be an int or a string
        if data.attr_type == AttrType.ENUM:
            for name, value in data.enum_fields:
                mfn.addField(name, value)
            dv = data.default_value
            if isinstance(dv, str):
                mfn.setDefaultByName(dv)
            else:
                # if it's not a string, assume it's an int
                mfn.default = dv

        # For the UNIT and NUMERIC type, set the bounds and soft bounds if any were provided
        if data.attr_type in (AttrType.UNIT, AttrType.NUMERIC):
            if data.min is not None:
                mfn.setMin(data.min)
            if data.max is not None:
                mfn.setMax(data.max)
            if data.soft_min is not None:
                mfn.setSoftMin(data.soft_min)
            if data.soft_max is not None:
                mfn.setSoftMax(data.soft_max)

        # For the STRING type, apply the optional as_filename parameter
        if data.attr_type == AttrType.STRING:
            mfn.usedAsFilename = data.as_filename

        mfn.array = data.multi
        if data.multi:
            mfn.indexMatters = data.index_matters
        mfn.keyable = data.keyable
        mfn.readable = data.readable

        return mfn

@dataclass
class UserClassData:
    user_class:type
    parent_class:type
    validator:Callable

class UserClassManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
        return cls._instance

    def __init__(self):
        self._by_user_class = {}
        self._by_parent_class = {}

    def register(self, user_class:type, validator:Union[Callable, str]):
        if isinstance(validator, str):
            validator = getattr(user_class, validator)

        # Create a Data object for this class
        parent_cls = self.get_parent_class(user_class)
        data = UserClassData(user_class=user_class, parent_class=parent_cls, validator=validator)

        # Check if there is already an entry for this parent class. If not, create an empty one
        if parent_cls not in self._by_parent_class:
            self._by_parent_class[parent_cls] = []

        # Remove duplicates (classes with the same name and module) to keep the registry clean
        for each_data in self._by_parent_class[parent_cls]:
            other_cls = each_data.user_class
            if other_cls.__name__ == user_class.__name__ and other_cls.__module__ == user_class.__module__:
                self.unregister(other_cls)

        # Add the UserClass data to each dict
        self._by_parent_class[parent_cls].append(data)
        self._by_user_class[user_class] = data

    @classmethod
    def get_parent_class(cls, user_class:type):

        package = inspect.getmodule(cls).__package__
        for each in inspect.getmro(user_class):
            if each.__module__.startswith(package) and each is not AbstractUserClass:
                parent_cls = each
                return parent_cls
        raise TypeError(f'{user_class} is not a subclass of an OMWrapper entity')

    def unregister(self, user_class:type):
        try:
            user_class_data = self._by_user_class.pop(user_class)
        except KeyError:
            raise ValueError(f'{user_class} was not registered as a user class')

        self._by_parent_class[user_class_data.parent_class].remove(user_class_data)

    def get_user_class(self, parent_class:type, obj:Union[str, om.MObject]):
        if parent_class in self._by_parent_class:
            data = self._by_parent_class[parent_class]
            if isinstance(obj, str):
                obj = name_to_api(obj, as_mobject=True)

            for d in data:
                if d.validator(obj):
                    return d.user_class
        raise ValueError(f'Cannot find a {parent_class.__name__} subclass for the provided object')

    def get_user_class_data(self, user_class:type):
        data = self._by_user_class.get(user_class)
        if data is None:
            raise ValueError(f'No data found for class {user_class.__name__}')
        return data

    def has_base_class(self, parent_class):
        return parent_class in self._by_parent_class

    def has_user_class(self, user_class):
        return user_class in self._by_user_class

user_class_manager = UserClassManager()
pyobject = PyObject()

class AbstractUserClass(ABC):
    NODE_TYPE: str
    BASE_TYPE: str

    @classmethod
    @abstractmethod
    def validator(cls, obj:om.MObject) -> bool:
        """
        The validation process to verify if a given node is a valid choice for this class

        Args:
            obj (MObject): the object to test

        Returns:
            bool: True if the object is valid. False otherwise

        """

    @classmethod
    @abstractmethod
    def _pre_create(cls, *args, **kwargs) -> Tuple[dict, dict]:
        """
        Operations that should happen before the node creation. Essentially, processing the parameters and splitting
        them to send them toward the create and post_create methods

        Subclasses may override this according to their needs

        Returns:
            List: Two dicts, the first one will be passed to _create and the second to _post_create

        """
        ...


    @classmethod
    @abstractmethod
    def _create(cls, **kwargs) -> Union[str, om.MObject]:
        """
        The actual node creation. There shouldn't be much more here.

        Subclasses may override this according to their needs

        Args:
            **kwargs: parameters issued from the _pre_create method

        Returns:
            str, MObject: The node that has been created

        """
        ...

    @classmethod
    @abstractmethod
    def _post_create(cls, node:Union[str, om.MObject], **kwargs):
        """
        Operations that should happen after the node creation

        Subclasses may override this according to their needs

        Args:
            node: the node created in the _create method
            **kwargs: the parameters processed in the _pre_create method

        Returns:

        """
        ...

    @classmethod
    def create(cls, *args, **kwargs):
        """
        The whole node creation process

        Returns:
            MayaObject: the newly created node

        """
        pre, post = cls._pre_create(*args, **kwargs)
        node = cls._create(**pre)
        cls._post_create(node, **post)

        return pyobject(node)

